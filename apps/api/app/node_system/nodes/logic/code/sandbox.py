"""Sandboxed execution for the Code node.

Two executors behind one entrypoint (`execute_code`):

- ProcessExecutor (phase A): runs user code in a separate, resource-limited
  process with a clean environment. Stops in-process secret access and DoS, but
  the child can still reach the network and filesystem.
- ContainerExecutor (phase B): runs user code in an ephemeral, locked-down
  container — no network, read-only fs, all capabilities dropped, non-root,
  resource-capped. A real isolation boundary.

Selection is driven by `settings.CODE_SANDBOX`:
- "auto" (default): container when a Docker runtime is reachable, else process.
- "container": require the container boundary (error in prod if Docker missing).
- "process": in-process hardening only.

Both executors share one I/O contract: stdin carries {"code","input"} (Python)
and stdout returns {"output","logs"} — so the bootstrap/wrapper are identical
whether run locally or inside a container.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import textwrap
import uuid
from contextlib import suppress
from typing import Any

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

_PROC_MEM_LIMIT_BYTES = 512 * 1024 * 1024
_FSIZE_LIMIT_BYTES = 16 * 1024 * 1024

# Fixed bootstrap (no user interpolation → no quoting/format hazards). Reads
# {"code","input"} from stdin, execs the user code, writes {"output","logs"} to
# stdout; user stdout/stderr are captured as logs.
_PY_BOOTSTRAP = r"""
import sys, json, io, math, re, datetime, collections
from contextlib import redirect_stdout, redirect_stderr

_payload = json.loads(sys.stdin.read())
_ns = {
    "__builtins__": __builtins__,
    "input": _payload.get("input", {}),
    "output": {},
    "logs": [],
    "json": json, "math": math, "re": re,
    "datetime": datetime, "collections": collections,
}
_out, _err = io.StringIO(), io.StringIO()
try:
    with redirect_stdout(_out), redirect_stderr(_err):
        exec(compile(_payload.get("code", ""), "<user-code>", "exec"), _ns)
except Exception as exc:
    sys.stderr.write(repr(exc))
    sys.exit(1)

_output = _ns.get("output", {})
if not isinstance(_output, dict):
    _output = {"result": _output}
_logs = [str(x) for x in _ns.get("logs", [])]
for _chunk in (_out.getvalue(), _err.getvalue()):
    _logs.extend(line for line in _chunk.strip().splitlines() if line)
sys.stdout.write(json.dumps({"output": _output, "logs": _logs}))
"""

_JS_WRAPPER = """\
const input = {input_json};
let output = {{}};
const logs = [];
const console = {{ log: (...a) => logs.push(a.map(String).join(' ')), error: (...a) => logs.push(a.map(String).join(' ')) }};
{code}
process.stdout.write(JSON.stringify({{ output, logs }}));
"""


def _sandbox_env() -> dict[str, str]:
    """Minimal environment for the local-process executor — omits worker secrets."""
    return {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"}


def _resource_limits(cpu_seconds: int):
    """preexec_fn capping CPU/file-size (+ memory on Linux). POSIX only."""
    if os.name != "posix":
        return None

    def _apply() -> None:
        import resource

        with suppress(ValueError, OSError):
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds + 1, cpu_seconds + 1))
        with suppress(ValueError, OSError):
            resource.setrlimit(resource.RLIMIT_FSIZE, (_FSIZE_LIMIT_BYTES, _FSIZE_LIMIT_BYTES))
        if sys.platform == "linux":
            with suppress(ValueError, OSError):
                resource.setrlimit(
                    resource.RLIMIT_AS, (_PROC_MEM_LIMIT_BYTES, _PROC_MEM_LIMIT_BYTES)
                )

    return _apply


async def _spawn(argv, stdin_bytes, timeout, *, env=None, preexec_fn=None, on_timeout=None):
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        preexec_fn=preexec_fn,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(stdin_bytes), timeout=timeout)
    except TimeoutError:
        if on_timeout is not None:
            with suppress(Exception):
                await on_timeout()
        with suppress(ProcessLookupError):
            proc.kill()
        await proc.wait()
        raise TimeoutError(f"Code execution timed out after {timeout}s") from None
    return out, err, proc.returncode or 0


def _parse_output(stdout_b: bytes) -> tuple[dict[str, Any], list[str]]:
    raw = stdout_b.decode("utf-8", errors="replace").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Unexpected code output (not JSON): {raw[:200]}") from e
    output = result.get("output", {})
    if not isinstance(output, dict):
        output = {"result": output}
    return output, result.get("logs", [])


def _py_payload(code: str, input_data: dict[str, Any]) -> bytes:
    return json.dumps({"code": textwrap.dedent(code), "input": input_data}).encode("utf-8")


class ProcessExecutor:
    """Phase A — hardened local subprocess."""

    async def run(self, language, code, input_data, timeout):
        if language == "python":
            argv = [sys.executable, "-I", "-B", "-c", _PY_BOOTSTRAP]
            stdin = _py_payload(code, input_data)
        elif language == "javascript":
            node = shutil.which("node")
            if not node:
                raise RuntimeError("Node.js not found. Install Node.js to run JavaScript code.")
            argv = [node, "-e", _JS_WRAPPER.format(input_json=json.dumps(input_data), code=code)]
            stdin = None
        else:
            raise RuntimeError(f"Unsupported language: {language}")

        out, err, rc = await _spawn(
            argv, stdin, timeout, env=_sandbox_env(), preexec_fn=_resource_limits(timeout)
        )
        if rc != 0:
            raise RuntimeError(err.decode("utf-8", errors="replace").strip() or "Execution failed")
        return _parse_output(out)


class ContainerExecutor:
    """Phase B — ephemeral, locked-down container per execution."""

    async def run(self, language, code, input_data, timeout):
        name = f"runmycrew-exec-{uuid.uuid4().hex}"
        flags = [
            "run",
            "--rm",
            "-i",
            "--name",
            name,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:size=64m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "256",
            "--memory",
            f"{settings.CODE_SANDBOX_MEMORY_MB}m",
            "--cpus",
            "1",
            "--user",
            "65534:65534",
        ]
        if language == "python":
            cmd = [settings.CODE_SANDBOX_PYTHON_IMAGE, "python", "-I", "-B", "-c", _PY_BOOTSTRAP]
            stdin = _py_payload(code, input_data)
        elif language == "javascript":
            wrapper = _JS_WRAPPER.format(input_json=json.dumps(input_data), code=code)
            cmd = [settings.CODE_SANDBOX_NODE_IMAGE, "node", "-e", wrapper]
            stdin = None
        else:
            raise RuntimeError(f"Unsupported language: {language}")

        async def _kill():
            with suppress(Exception):
                p = await asyncio.create_subprocess_exec(
                    "docker",
                    "kill",
                    name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await p.wait()

        out, err, rc = await _spawn(["docker", *flags, *cmd], stdin, timeout, on_timeout=_kill)
        if rc != 0:
            raise RuntimeError(err.decode("utf-8", errors="replace").strip() or "Execution failed")
        return _parse_output(out)


_docker_ok: bool | None = None


async def docker_available() -> bool:
    """Cached check that a Docker runtime is reachable."""
    global _docker_ok
    if _docker_ok is not None:
        return _docker_ok
    if not shutil.which("docker"):
        _docker_ok = False
        return _docker_ok
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "info", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(proc.wait(), timeout=8)
        _docker_ok = proc.returncode == 0
    except Exception:
        _docker_ok = False
    return _docker_ok


async def execute_code(
    language: str, code: str, input_data: dict[str, Any], timeout: int
) -> tuple[dict[str, Any], list[str]]:
    mode = settings.CODE_SANDBOX
    if mode == "process":
        use_container = False
    elif mode == "container":
        if not await docker_available():
            if settings.ENVIRONMENT == "production":
                raise RuntimeError("CODE_SANDBOX=container but no Docker runtime is available.")
            logger.warning("CODE_SANDBOX=container but Docker unavailable; using process executor.")
            use_container = False
        else:
            use_container = True
    else:  # auto
        use_container = await docker_available()

    executor = ContainerExecutor() if use_container else ProcessExecutor()
    return await executor.run(language, code, input_data, timeout)

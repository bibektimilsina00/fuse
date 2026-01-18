import builtins
import logging
import re
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Import request ID context
from fuse.utils.request_id import get_request_id

# Custom theme for automation platform
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "error": "bold red",
        "task": "bold yellow",
        "node": "bold blue",
        "engine": "bold green",
    }
)

console = Console(theme=custom_theme)


class CompactFilter(logging.Filter):
    """Filters log messages to shorten UUIDs and float numbers for technical density."""

    # Regex for UUID (standard 8-4-4-4-12 format)
    UUID_PATTERN = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I
    )
    # Regex for long floats (3+ decimal places)
    FLOAT_PATTERN = re.compile(r"(\d+\.\d{4,})")

    def filter(self, record):
        if not isinstance(record.msg, str):
            return True

        # 1. Shorten package names first so they can be filtered/used later
        msg = record.msg
        msg = msg.replace(
            "fuse.workflows.engine.check_scheduled_workflows", "engine.periodic"
        )
        msg = msg.replace("fuse.workflows.engine.", "engine.")
        msg = msg.replace("Task engine.execute_workflow", "Workflow")

        # 2. Add request ID prefix if available
        request_id = get_request_id()
        if request_id:
            # Short request ID for logs (first 8 chars)
            short_id = request_id[:8]
            msg = f"[{short_id}] {msg}"

        # 2. Suppress heartbeat noise (only if result is 0 or it's just a status check)
        # Suppress 'Sending due task', 'received', 'Checking for', and 'succeeded: 0'
        noise_keywords = [
            "Sending due task",
            "received",
            "Checking for",
            "succeeded in",
        ]
        if "engine.periodic" in msg:
            if any(k in msg for k in ["received", "Sending due task", "Checking for"]):
                return False
            if "succeeded in" in msg and ": 0" in msg:
                return False

        # 3. Shorten UUIDs: a1e9166a-15f5-4ccf-b2ff-a6a92c37e645 -> a1e9..
        def shorten_uuid(match):
            val = match.group(0)
            return f"{val[:4]}.."

        # 4. Shorten Floats: 0.012413125... -> 0.012
        def shorten_float(match):
            val = float(match.group(0))
            return f"{val:.3f}"

        msg = self.UUID_PATTERN.sub(shorten_uuid, msg)
        msg = self.FLOAT_PATTERN.sub(shorten_float, msg)

        record.msg = msg
        return True


def setup_global_logger(log_level: str = "INFO"):
    """
    Configures a global logger using Rich for beautiful output.
    """
    # Create logger
    logger = logging.getLogger("fuse_backend")

    # Set level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            show_path=False,  # Compact: don't show the file path
            show_time=True,
            omit_repeated_times=True,
            keywords=[
                "workflow",
                "node",
                "engine",
                "task",
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
            ],
        )

        # Simple format for message only
        formatter = logging.Formatter("%(message)s", datefmt="[%X]")
        rich_handler.setFormatter(formatter)
        rich_handler.addFilter(CompactFilter())
        logger.addHandler(rich_handler)

    # Inject into builtins
    builtins.logger = logger

    return logger


def setup_celery_logger(logger=None, loglevel=None, **kwargs):
    """
    Hook for Celery after_setup_logger to format Celery logs beautifully.
    """
    if logger is None:
        logger = logging.getLogger("celery")

    # Apply compact Rich to Celery logs
    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            show_path=False,
            show_time=True,
        )
        rich_handler.addFilter(CompactFilter())
        logger.addHandler(rich_handler)

    return logger


# Export a module-level logger for simple imports
logger = logging.getLogger("fuse_backend")

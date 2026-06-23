"""Hard budget enforcement for agent loops.

The agent runtime checks one of these every iteration before calling
the LLM. Once any budget is exhausted the loop terminates with
``status='budget_exhausted'`` and the partial trace is preserved.

Wall-clock starts when the Budget is constructed (i.e. when the
agent's ``execute()`` begins). Iteration / token / cost counters
accumulate via ``add_iteration()`` and ``add_llm_usage()`` calls from
the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .pricing import cost_for_call

# Hard system caps. Workspaces can configure UP TO these values but
# never above. Defends against pathological workflow configs (e.g. a
# user setting max_iterations=10000) that would let one loop monopolise
# the worker.
SYSTEM_MAX_ITERATIONS = 100
SYSTEM_MAX_SECONDS = 60 * 60  # 1 h
SYSTEM_MAX_INPUT_TOKENS = 5_000_000  # 5 M tokens / loop fire
SYSTEM_MAX_COST_USD = 50.0


@dataclass
class Budget:
    """Mutable per-loop budget tracker.

    All ``max_*`` fields are caller-supplied and silently clamped to
    the corresponding ``SYSTEM_MAX_*`` ceiling on construction.

    Cost is computed from ``add_llm_usage(usage, provider, model)``
    rather than passed in pre-computed, so the runtime never has to
    know the price table.
    """

    max_iterations: int = SYSTEM_MAX_ITERATIONS
    max_seconds: int = SYSTEM_MAX_SECONDS
    max_input_tokens: int = SYSTEM_MAX_INPUT_TOKENS
    max_cost_usd: float = SYSTEM_MAX_COST_USD

    used_input_tokens: int = 0
    used_output_tokens: int = 0
    used_cost_usd: float = 0.0
    used_tool_calls: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Clamp to system ceiling. Don't error — a workflow author may
        # have set 999_999 thinking it's infinity; clamping to the cap
        # is friendlier than refusing to run.
        self.max_iterations = min(
            int(self.max_iterations or 0) or SYSTEM_MAX_ITERATIONS, SYSTEM_MAX_ITERATIONS
        )
        self.max_seconds = min(int(self.max_seconds or 0) or SYSTEM_MAX_SECONDS, SYSTEM_MAX_SECONDS)
        self.max_input_tokens = min(
            int(self.max_input_tokens or 0) or SYSTEM_MAX_INPUT_TOKENS, SYSTEM_MAX_INPUT_TOKENS
        )
        self.max_cost_usd = min(
            float(self.max_cost_usd or 0.0) or SYSTEM_MAX_COST_USD, SYSTEM_MAX_COST_USD
        )

    # ── Exhaustion checks ────────────────────────────────────────────

    def iterations_exhausted(self, iteration: int) -> bool:
        return iteration >= self.max_iterations

    def time_exhausted(self) -> bool:
        return self.wall_seconds() >= self.max_seconds

    def tokens_exhausted(self) -> bool:
        return self.used_input_tokens >= self.max_input_tokens

    def cost_exhausted(self) -> bool:
        return self.used_cost_usd >= self.max_cost_usd

    def any_exhausted(self, iteration: int) -> tuple[bool, str | None]:
        """Return ``(True, reason)`` if any budget is hit, else ``(False, None)``.

        ``reason`` is one of ``'iterations'|'time'|'tokens'|'cost'`` —
        suitable for storing on the run record so users can see why
        the loop stopped.
        """
        if self.iterations_exhausted(iteration):
            return True, "iterations"
        if self.time_exhausted():
            return True, "time"
        if self.tokens_exhausted():
            return True, "tokens"
        if self.cost_exhausted():
            return True, "cost"
        return False, None

    # ── Mutators ─────────────────────────────────────────────────────

    def add_llm_usage(
        self, *, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Record one LLM call. Returns the marginal cost of this call.

        Marginal cost is also added to ``used_cost_usd``. Callers can
        store the marginal value on the trace step.
        """
        self.used_input_tokens += int(input_tokens or 0)
        self.used_output_tokens += int(output_tokens or 0)
        marginal = cost_for_call(provider, model, input_tokens, output_tokens)
        self.used_cost_usd += marginal
        return marginal

    def add_tool_call(self) -> None:
        self.used_tool_calls += 1

    # ── Read-only accessors ──────────────────────────────────────────

    def wall_seconds(self) -> float:
        return (datetime.now(UTC) - self.started_at).total_seconds()

    def snapshot(self) -> dict[str, Any]:
        """Roll-up suitable for persistence on the run record.

        Schema kept stable — dashboards + bills query these keys.
        """
        return {
            "input_tokens": self.used_input_tokens,
            "output_tokens": self.used_output_tokens,
            "cost_usd": round(self.used_cost_usd, 6),
            "tool_calls": self.used_tool_calls,
            "wall_seconds": round(self.wall_seconds(), 3),
            "limits": {
                "max_iterations": self.max_iterations,
                "max_seconds": self.max_seconds,
                "max_input_tokens": self.max_input_tokens,
                "max_cost_usd": self.max_cost_usd,
            },
        }

"""Unit tests for the agent loop Budget + stop-condition + pricing.

These are pure-logic tests; they don't spin up the LLM or the
workflow runner.
"""

from __future__ import annotations

import time

import pytest

from apps.api.app.node_system.nodes.ai.agent.budget import (
    SYSTEM_MAX_COST_USD,
    SYSTEM_MAX_INPUT_TOKENS,
    SYSTEM_MAX_ITERATIONS,
    SYSTEM_MAX_SECONDS,
    Budget,
)
from apps.api.app.node_system.nodes.ai.agent.pricing import (
    UNKNOWN_FALLBACK,
    cost_for_call,
    is_known,
)
from apps.api.app.node_system.nodes.ai.agent.stop_condition import (
    evaluate_success_when,
    expression_is_valid,
)

# ── Budget ─────────────────────────────────────────────────────────


class TestBudget:
    def test_defaults_to_system_caps_when_zero(self):
        b = Budget(max_iterations=0, max_seconds=0, max_input_tokens=0, max_cost_usd=0.0)
        assert b.max_iterations == SYSTEM_MAX_ITERATIONS
        assert b.max_seconds == SYSTEM_MAX_SECONDS
        assert b.max_input_tokens == SYSTEM_MAX_INPUT_TOKENS
        assert b.max_cost_usd == SYSTEM_MAX_COST_USD

    def test_clamps_above_system_cap(self):
        b = Budget(
            max_iterations=999_999,
            max_seconds=999_999,
            max_input_tokens=999_999_999,
            max_cost_usd=999_999.0,
        )
        assert b.max_iterations == SYSTEM_MAX_ITERATIONS
        assert b.max_seconds == SYSTEM_MAX_SECONDS
        assert b.max_input_tokens == SYSTEM_MAX_INPUT_TOKENS
        assert b.max_cost_usd == SYSTEM_MAX_COST_USD

    def test_iteration_cap(self):
        b = Budget(max_iterations=3)
        assert b.iterations_exhausted(0) is False
        assert b.iterations_exhausted(2) is False
        assert b.iterations_exhausted(3) is True
        assert b.iterations_exhausted(99) is True

    def test_token_cap_via_llm_usage(self):
        b = Budget(max_input_tokens=1_000)
        b.add_llm_usage(provider="openai", model="gpt-5", input_tokens=400, output_tokens=200)
        assert b.tokens_exhausted() is False
        b.add_llm_usage(provider="openai", model="gpt-5", input_tokens=600, output_tokens=200)
        assert b.tokens_exhausted() is True

    def test_cost_cap_via_llm_usage(self):
        # gpt-5 is $5/M input, $15/M output → 1M input + 0 output = $5
        b = Budget(max_cost_usd=4.0)
        b.add_llm_usage(provider="openai", model="gpt-5", input_tokens=1_000_000, output_tokens=0)
        assert b.cost_exhausted() is True

    def test_time_cap(self):
        b = Budget(max_seconds=1)
        assert b.time_exhausted() is False
        time.sleep(1.05)
        assert b.time_exhausted() is True

    def test_any_exhausted_returns_first_breach_reason(self):
        b = Budget(max_iterations=2)
        ok, why = b.any_exhausted(2)
        assert ok is True
        assert why == "iterations"

    def test_snapshot_shape_stable(self):
        b = Budget(max_iterations=5, max_seconds=60, max_input_tokens=10_000, max_cost_usd=0.10)
        b.add_llm_usage(provider="openai", model="gpt-5-mini", input_tokens=100, output_tokens=20)
        b.add_tool_call()
        snap = b.snapshot()
        # required keys for dashboards
        assert set(snap.keys()) >= {
            "input_tokens",
            "output_tokens",
            "cost_usd",
            "tool_calls",
            "wall_seconds",
            "limits",
        }
        assert snap["input_tokens"] == 100
        assert snap["output_tokens"] == 20
        assert snap["tool_calls"] == 1
        assert snap["cost_usd"] > 0
        assert snap["limits"]["max_iterations"] == 5

    def test_zero_usage_is_zero_cost(self):
        b = Budget()
        marginal = b.add_llm_usage(
            provider="openai", model="gpt-5", input_tokens=0, output_tokens=0
        )
        assert marginal == 0.0


# ── Pricing ────────────────────────────────────────────────────────


class TestPricing:
    @pytest.mark.parametrize(
        "provider,model",
        [
            ("openai", "gpt-5"),
            ("anthropic", "claude-opus-4-7"),
            ("google", "gemini-2.5-pro"),
            ("groq", "llama-3.3-70b-versatile"),
        ],
    )
    def test_known_models_have_prices(self, provider, model):
        assert is_known(provider, model) is True
        cost = cost_for_call(provider, model, input_tokens=1_000_000, output_tokens=0)
        assert cost > 0

    def test_unknown_model_falls_back(self):
        assert is_known("openai", "totally-made-up-model") is False
        cost = cost_for_call(
            "openai", "totally-made-up-model", input_tokens=1_000_000, output_tokens=0
        )
        assert cost == UNKNOWN_FALLBACK[0]  # in_rate * 1M / 1M = in_rate USD

    def test_provider_case_insensitive(self):
        a = cost_for_call("OPENAI", "gpt-5", 1000, 500)
        b = cost_for_call("openai", "gpt-5", 1000, 500)
        assert a == b


# ── success_when ───────────────────────────────────────────────────


class TestSuccessWhen:
    def test_empty_expression_always_satisfied(self):
        assert evaluate_success_when(None, {"action_taken": False}) is True
        assert evaluate_success_when("", {"action_taken": False}) is True
        assert evaluate_success_when("   ", {"x": 1}) is True

    def test_truthy_field(self):
        assert evaluate_success_when("action_taken", {"action_taken": True}) is True
        assert evaluate_success_when("action_taken", {"action_taken": False}) is False

    def test_equality(self):
        assert evaluate_success_when('status = "done"', {"status": "done"}) is True
        assert evaluate_success_when('status = "done"', {"status": "pending"}) is False

    def test_compound(self):
        # Both action taken AND status done
        expr = 'action_taken and status = "done"'
        assert evaluate_success_when(expr, {"action_taken": True, "status": "done"}) is True
        assert evaluate_success_when(expr, {"action_taken": True, "status": "pending"}) is False

    def test_malformed_expression_treated_as_satisfied(self):
        # Don't trap the loop on a bad user expression — log + move on.
        assert evaluate_success_when("$.invalid syntax (", {"x": 1}) is True

    def test_expression_validator(self):
        ok, _err = expression_is_valid("action_taken")
        assert ok is True
        ok, err = expression_is_valid("(((invalid")
        # Pure-python jsonata may or may not reject this at parse time; we
        # only assert the function doesn't blow up.
        assert ok in (True, False)
        if not ok:
            assert isinstance(err, str)

    def test_none_result(self):
        # Agent returned None — expression should evaluate fine
        # (most expressions on None are falsy).
        assert evaluate_success_when("action_taken", None) is False

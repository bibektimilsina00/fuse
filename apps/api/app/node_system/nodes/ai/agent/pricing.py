"""Per-model price table for LLM calls.

Used by ``Budget.add_llm_usage()`` to compute marginal cost. Prices
are in USD per million tokens, current as of 2026-Q2.

Update procedure:
1. Find the model's pricing page (Anthropic, OpenAI, Google, etc).
2. Add / update the row.
3. Run ``pytest apps/api/tests/node_system/ai/agent/test_pricing.py``.

Unknown models default to ``UNKNOWN_FALLBACK`` so a brand-new model
release doesn't crash the runtime; the cost row gets a sensible
floor estimate. Users see a warning in the trace if their model is
unknown.
"""

from __future__ import annotations

# Per-million-token prices: (input USD/M, output USD/M).
_PRICES: dict[tuple[str, str], tuple[float, float]] = {
    # ── Anthropic ────────────────────────────────────────────────
    ("anthropic", "claude-opus-4-7"): (15.0, 75.0),
    ("anthropic", "claude-opus-4-6"): (15.0, 75.0),
    ("anthropic", "claude-opus-4-5"): (15.0, 75.0),
    ("anthropic", "claude-opus-4-0"): (15.0, 75.0),
    ("anthropic", "claude-sonnet-4-6"): (3.0, 15.0),
    ("anthropic", "claude-sonnet-4-5"): (3.0, 15.0),
    ("anthropic", "claude-sonnet-4-0"): (3.0, 15.0),
    ("anthropic", "claude-haiku-4-5-20251001"): (1.0, 5.0),
    ("anthropic", "claude-haiku-4-5"): (1.0, 5.0),
    ("anthropic", "claude-3-7-sonnet-20250219"): (3.0, 15.0),
    ("anthropic", "claude-3-5-haiku-20241022"): (0.8, 4.0),
    # ── OpenAI ───────────────────────────────────────────────────
    ("openai", "gpt-5"): (5.0, 15.0),
    ("openai", "gpt-5-mini"): (0.4, 1.6),
    ("openai", "gpt-5-nano"): (0.1, 0.4),
    ("openai", "gpt-4o"): (2.5, 10.0),
    ("openai", "gpt-4o-mini"): (0.15, 0.6),
    ("openai", "gpt-4-turbo"): (10.0, 30.0),
    ("openai", "o1"): (15.0, 60.0),
    ("openai", "o3"): (15.0, 60.0),
    ("openai", "o3-mini"): (1.1, 4.4),
    ("openai", "o4-mini"): (3.0, 12.0),
    # ── Google Gemini ────────────────────────────────────────────
    ("google", "gemini-2.5-pro"): (2.5, 10.0),
    ("google", "gemini-2.5-flash"): (0.3, 2.5),
    ("google", "gemini-2.5-flash-lite"): (0.1, 0.4),
    ("google", "gemini-2.0-flash"): (0.1, 0.4),
    ("google", "gemini-1.5-pro"): (1.25, 5.0),
    ("google", "gemini-1.5-flash"): (0.075, 0.3),
    # ── Groq ─────────────────────────────────────────────────────
    ("groq", "llama-3.3-70b-versatile"): (0.59, 0.79),
    ("groq", "llama-3.1-8b-instant"): (0.05, 0.08),
    ("groq", "mixtral-8x7b-32768"): (0.24, 0.24),
    ("groq", "deepseek-r1-distill-llama-70b"): (0.75, 0.99),
    # ── Mistral ──────────────────────────────────────────────────
    ("mistral", "mistral-large-latest"): (2.0, 6.0),
    ("mistral", "mistral-medium-latest"): (2.7, 8.1),
    ("mistral", "mistral-small-latest"): (0.2, 0.6),
    # ── DeepSeek ─────────────────────────────────────────────────
    ("deepseek", "deepseek-chat"): (0.27, 1.10),
    ("deepseek", "deepseek-reasoner"): (0.55, 2.19),
    # ── xAI ──────────────────────────────────────────────────────
    ("xai", "grok-3"): (3.0, 15.0),
    ("xai", "grok-3-mini"): (0.3, 0.5),
    ("xai", "grok-4"): (5.0, 25.0),
    # ── Perplexity (Sonar) ───────────────────────────────────────
    ("perplexity", "sonar"): (1.0, 1.0),
    ("perplexity", "sonar-pro"): (3.0, 15.0),
    ("perplexity", "sonar-reasoning"): (1.0, 5.0),
    # ── Together AI (common open-weight stops) ───────────────────
    ("together", "meta-llama/Llama-3.3-70B-Instruct-Turbo"): (0.88, 0.88),
    ("together", "meta-llama/Llama-3.1-405B-Instruct-Turbo"): (3.5, 3.5),
    ("together", "Qwen/Qwen2.5-72B-Instruct-Turbo"): (1.2, 1.2),
    # ── Fireworks ────────────────────────────────────────────────
    ("fireworks", "accounts/fireworks/models/llama-v3p3-70b-instruct"): (0.9, 0.9),
    ("fireworks", "accounts/fireworks/models/qwen2p5-72b-instruct"): (0.9, 0.9),
    # ── OpenRouter — proxies everything; fallback estimate ───────
    # Don't enumerate every model; UNKNOWN_FALLBACK applies. Users
    # who care should specify the upstream provider directly to get
    # accurate pricing.
}

# Conservative floor: assumes a small mid-tier model. We'd rather over-
# bill the budget enforcer than let an unknown-pricing model run free.
UNKNOWN_FALLBACK: tuple[float, float] = (5.0, 15.0)


def cost_for_call(provider: str, model: str | None, input_tokens: int, output_tokens: int) -> float:
    """Compute the USD cost for a single LLM call.

    Returns 0.0 if both token counts are 0 (no charge for an empty
    call). Always returns a float rounded to 6 decimals.
    """
    if not input_tokens and not output_tokens:
        return 0.0

    key = (provider.lower() if provider else "", (model or "").strip())
    in_rate, out_rate = _PRICES.get(key, UNKNOWN_FALLBACK)
    cost = (input_tokens / 1_000_000.0) * in_rate + (output_tokens / 1_000_000.0) * out_rate
    return round(cost, 6)


def is_known(provider: str, model: str | None) -> bool:
    """True when (provider, model) has an explicit price row.

    The runtime surfaces a one-time warning per loop fire when the
    model is unknown so users notice their cost row is approximate.
    """
    return (provider.lower() if provider else "", (model or "").strip()) in _PRICES

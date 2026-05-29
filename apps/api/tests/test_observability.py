"""Sentry init is a safe no-op unless a DSN is configured."""

from apps.api.app.core import observability


def test_init_sentry_is_noop_without_dsn(monkeypatch):
    monkeypatch.setattr(observability.settings, "SENTRY_DSN", "")
    monkeypatch.setattr(observability, "_initialized", False)

    observability.init_sentry()  # must not raise and must not initialize

    assert observability._initialized is False

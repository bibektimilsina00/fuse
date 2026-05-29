"""Production must refuse the shipped default/empty secrets.

Without this, a deployment left on defaults has a publicly-known JWT signing key
(forgeable tokens) and a publicly-known credential-encryption key (all stored
secrets decryptable). The validator fails startup in production; dev keeps the
convenient defaults.
"""

import pytest

from apps.api.app.core.config import Settings

_DEFAULTS = Settings.model_fields


def test_production_rejects_default_secrets():
    with pytest.raises(ValueError, match="production"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY=_DEFAULTS["SECRET_KEY"].default,
            ENCRYPTION_KEY=_DEFAULTS["ENCRYPTION_KEY"].default,
        )


def test_production_rejects_empty_secrets():
    with pytest.raises(ValueError, match="production"):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="", ENCRYPTION_KEY="")


def test_production_accepts_strong_secrets():
    s = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SECRET_KEY="a" * 48,
        ENCRYPTION_KEY="b" * 44,
    )
    assert s.ENVIRONMENT == "production"


def test_development_allows_defaults():
    s = Settings(_env_file=None, ENVIRONMENT="development")
    assert s.SECRET_KEY  # defaults are fine in dev — no raise

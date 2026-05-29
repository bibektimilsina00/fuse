"""Credential encryption (AESEncryptionService) round-trips across key formats."""

from cryptography.fernet import Fernet

from apps.api.app.credential_manager.encryption.aes import AESEncryptionService


def test_encrypts_and_decrypts_with_fernet_key():
    svc = AESEncryptionService(key=Fernet.generate_key().decode())  # 44-char Fernet key
    token = svc.encrypt("secret-value")
    assert token != "secret-value"
    assert svc.decrypt(token) == "secret-value"


def test_accepts_hex_key_from_openssl_rand():
    # `openssl rand -hex 32` produces 64 hex chars — the key the README recommends.
    svc = AESEncryptionService(key="a" * 64)
    assert svc.decrypt(svc.encrypt("hello")) == "hello"


def test_same_key_decrypts_across_instances():
    # API and Worker construct separate services; the same key must interoperate.
    key = "c" * 64
    api = AESEncryptionService(key=key)
    worker = AESEncryptionService(key=key)
    assert worker.decrypt(api.encrypt("shared")) == "shared"

import base64
from fuse.config import settings

def _get_key_bytes() -> bytes:
    # Ensure key is long enough or cycle it. SECRET_KEY is usually 32+ chars.
    return settings.SECRET_KEY.encode()

def encrypt_string(raw: str) -> str:
    """
    Encrypts a string using a simple XOR cipher with the application SECRET_KEY.
    NOTE: This is a basic obfuscation for MVP. For production, use libraries like 
    Wait 'cryptography' and Fernet.
    """
    if not raw: return raw
    key = _get_key_bytes()
    raw_bytes = raw.encode()
    encrypted = bytearray()
    for i in range(len(raw_bytes)):
        encrypted.append(raw_bytes[i] ^ key[i % len(key)])
    return base64.b64encode(encrypted).decode()

def decrypt_string(enc: str) -> str:
    """
    Decrypts a string encrypted with encrypt_string.
    """
    if not enc: return enc
    try:
        key = _get_key_bytes()
        enc_bytes = base64.b64decode(enc)
        decrypted = bytearray()
        for i in range(len(enc_bytes)):
            decrypted.append(enc_bytes[i] ^ key[i % len(key)])
        return decrypted.decode()
    except Exception:
        # If decryption fails (maybe it wasn't encrypted), return original
        return enc

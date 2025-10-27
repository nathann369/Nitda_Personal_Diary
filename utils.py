# utils.py
# Helpers: date parsing + encryption helpers (Fernet key derivation)

import base64
import re
from datetime import datetime
from typing import Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend


def parse_date(date_str: Optional[str]):
    """Validate YYYY-MM-DD or return None."""
    if not date_str:
        return None
    date_str = date_str.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        # will raise ValueError if invalid date
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    raise ValueError("Date must be YYYY-MM-DD")


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible 32-byte key from a password and salt."""
    # PBKDF2HMAC to derive 32 bytes, then base64-url-safe for Fernet
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(key)


def encrypt_text(password: str, plaintext: str) -> dict:
    """
    Encrypt plaintext with a password.
    Returns a dict with 'salt' and 'token' (both base64 str).
    """
    salt = base64.urlsafe_b64encode(__import__("os").urandom(16))
    salt_bytes = base64.urlsafe_b64decode(salt)
    key = derive_key_from_password(password, salt_bytes)
    f = Fernet(key)
    token = f.encrypt(plaintext.encode())
    return {"salt": salt.decode(), "token": base64.b64encode(token).decode()}


def decrypt_text(password: str, blob: dict) -> str:
    """Decrypt blob returned by encrypt_text using same password."""
    salt_b64 = blob.get("salt")
    token_b64 = blob.get("token")
    if not salt_b64 or not token_b64:
        raise ValueError("Invalid encrypted blob.")
    salt_bytes = base64.urlsafe_b64decode(salt_b64)
    key = derive_key_from_password(password, salt_bytes)
    f = Fernet(key)
    token = base64.b64decode(token_b64)
    return f.decrypt(token).decode()

import json
import os
import hashlib
import base64
import secrets

USERS_FILE = "users.json"


def _load_users():
    """Load user data from file."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users):
    """Save user data to file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def hash_password(password: str):
    """Generate a secure hash using PBKDF2."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.b64encode(salt + key).decode()


def verify_password(stored_hash: str, password: str):
    """Verify a password against stored hash."""
    data = base64.b64decode(stored_hash.encode())
    salt, key = data[:16], data[16:]
    new_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return new_key == key


def signup(username: str, password: str):
    """Register a new user."""
    users = _load_users()
    if username in users:
        return False, "Username already exists!"
    users[username] = {"password": hash_password(password)}
    _save_users(users)
    return True, "Account created successfully!"


def login(username: str, password: str):
    """Validate login credentials."""
    users = _load_users()
    if username not in users:
        return False, "User not found!"
    stored_hash = users[username]["password"]
    if verify_password(stored_hash, password):
        return True, "Login successful!"
    return False, "Incorrect password!"

import os
from utils import hash_text

PASSWORD_FILE = 'password.txt'

def save_password(password: str):
    with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
        f.write(hash_text(password))

def verify_password(entered: str) -> bool:
    # If file doesn't exist, create it using this password
    if not os.path.exists(PASSWORD_FILE):
        save_password(entered)
        return True
    with open(PASSWORD_FILE, 'r', encoding='utf-8') as f:
        stored = f.read().strip()
    return stored == hash_text(entered)

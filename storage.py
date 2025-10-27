# storage.py
# Simple JSON per-user storage helpers

import os
import json
from typing import Dict, Any

DATA_DIR = "data"


def user_data_path(username: str) -> str:
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"data_{username}.json")


def ensure_user_file(username: str):
    path = user_data_path(username)
    if not os.path.exists(path):
        # initialize with empty entries list
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": []}, f, indent=2)


def load_entries(username: str):
    path = user_data_path(username)
    ensure_user_file(username)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entries", [])


def save_entries(username: str, entries):
    path = user_data_path(username)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f, indent=2)

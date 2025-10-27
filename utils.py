import hashlib, re

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def validate_date(date_str: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))

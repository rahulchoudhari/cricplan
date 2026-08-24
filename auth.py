# auth.py
import re

import bcrypt

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)\S{8,64}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_RE.match(username))


def is_valid_password(password: str) -> bool:
    return bool(PASSWORD_RE.match(password))


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))

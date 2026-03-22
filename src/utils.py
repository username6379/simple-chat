import random
from dataclasses import dataclass
from datetime import datetime, timezone


def generate_id() -> str:
    return str(random.randint(100_000, 999_999))


def generate_session_id():
    return 'S' + generate_id()


def generate_chat_id():
    return 'C' + generate_id()


def get_current_time():
    return datetime.now(timezone.utc)


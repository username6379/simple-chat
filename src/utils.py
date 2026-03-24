import random


def generate_id() -> str:
    return str(random.randint(100_000, 999_999))


def generate_session_id():
    return 'S' + generate_id()

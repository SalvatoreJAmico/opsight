import os


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


API_BASE_URL = _get_env("API_BASE_URL").rstrip("/")
STORAGE_PATH = _get_env("STORAGE_PATH")

import os


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


API_BASE_URL = get_required_env("API_BASE_URL").rstrip("/")
STORAGE_PATH = get_required_env("STORAGE_PATH")
PIPELINE_SUMMARY_PATH = get_required_env("PIPELINE_SUMMARY_PATH")

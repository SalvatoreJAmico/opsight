import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOCAL_ENV_PATH = PROJECT_ROOT / ".env"


def load_local_env_file(env_path: Path = LOCAL_ENV_PATH) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")

        if name and os.getenv(name) is None:
            os.environ[name] = value


def get_config_value(name: str, *, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is not None and value.strip() != "":
        return value.strip()

    if default is not None:
        return default

    env_hint = f"Set {name} in the environment or add it to {LOCAL_ENV_PATH.name} at the repository root."
    raise RuntimeError(f"Missing required Streamlit config: {name}. {env_hint}")


load_local_env_file()

API_BASE_URL = get_config_value("API_BASE_URL", default="http://127.0.0.1:8000").rstrip("/")
STORAGE_PATH = get_config_value("STORAGE_PATH", default=str(PROJECT_ROOT / "data" / "records.json"))
PIPELINE_SUMMARY_PATH = get_config_value(
    "PIPELINE_SUMMARY_PATH",
    default=str(PROJECT_ROOT / "reports" / "pipeline_run_summary.json"),
)

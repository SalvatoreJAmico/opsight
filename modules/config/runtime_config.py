import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


logger = logging.getLogger("opsight.config")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ENV_PATH = PROJECT_ROOT / ".env"


def _raise_runtime_config_error(message: str, *, cause: Optional[Exception] = None) -> None:
    logger.error(
        "Runtime configuration error",
        extra={
            "event": "runtime_config_error",
            "error_type": "runtime_config_error",
            "error_message": message,
        },
    )
    if cause:
        raise RuntimeError(message) from cause
    raise RuntimeError(message)


def load_local_env_file(env_path: Optional[Path] = None) -> None:
    resolved_env_path = env_path or LOCAL_ENV_PATH
    if not resolved_env_path.exists():
        return

    for raw_line in resolved_env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")

        if name and os.getenv(name) is None:
            os.environ[name] = value


@dataclass(frozen=True)
class RuntimeConfig:
    app_env: str
    app_version: str
    port: int
    upload_access_code: str
    persistence_mode: str
    storage_path: str
    log_level: str
    allow_local_fallback: bool
    blob_account: Optional[str]
    blob_container: Optional[str]
    blob_path: Optional[str]
    api_base_url: Optional[str]
    enable_pipeline: bool
    input_source_path: Optional[str]
    pipeline_summary_path: Optional[str]
    azure_storage_connection_string: Optional[str]


def get_env(name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        _raise_runtime_config_error(
            f"Missing required environment variable: {name}. "
            f"Set it in the environment or add it to {LOCAL_ENV_PATH.name} at the repository root."
        )
    return value


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_runtime_config() -> RuntimeConfig:
    load_local_env_file()

    app_env = get_env("APP_ENV")
    if app_env not in {"dev", "prod"}:
        _raise_runtime_config_error("APP_ENV must be one of: dev, prod")

    app_version = get_env("APP_VERSION")
    port_raw = get_env("PORT")
    upload_access_code = get_env("UPLOAD_ACCESS_CODE")
    persistence_mode = get_env("PERSISTENCE_MODE")
    storage_path = get_env("STORAGE_PATH")
    log_level = get_env("LOG_LEVEL")

    try:
        port = int(port_raw)
    except ValueError as exc:
        _raise_runtime_config_error("Environment variable PORT must be an integer", cause=exc)

    allow_local_fallback = _to_bool(get_env("ALLOW_LOCAL_FALLBACK", required=False, default="true"), default=True)
    blob_account = get_env("BLOB_ACCOUNT", required=False, default=None)
    blob_container = get_env("BLOB_CONTAINER", required=False, default=None)
    blob_path = get_env("BLOB_PATH", required=False, default=None)
    api_base_url = get_env("API_BASE_URL", required=False, default=None)
    enable_pipeline = _to_bool(get_env("ENABLE_PIPELINE", required=False, default="true"), default=True)
    input_source_path = get_env("INPUT_SOURCE_PATH", required=False, default=None)
    pipeline_summary_path = get_env("PIPELINE_SUMMARY_PATH")
    azure_storage_connection_string = get_env("AZURE_STORAGE_CONNECTION_STRING", required=False, default=None)

    # ===== PRODUCTION MODE VALIDATION =====
    if app_env == "prod":
        # Production must NOT use local fallback
        if allow_local_fallback:
            _raise_runtime_config_error(
                "Local fallback is not allowed in production. "
                "Set ALLOW_LOCAL_FALLBACK=false in production."
            )

        # Production MUST have all three Blob parameters set
        if not blob_account or not blob_account.strip():
            _raise_runtime_config_error(
                "Production mode requires BLOB_ACCOUNT to be set. "
                "Blob is the mandatory ingestion source in production."
            )
        if not blob_container or not blob_container.strip():
            _raise_runtime_config_error(
                "Production mode requires BLOB_CONTAINER to be set. "
                "Blob is the mandatory ingestion source in production."
            )
        if not blob_path or not blob_path.strip():
            _raise_runtime_config_error(
                "Production mode requires BLOB_PATH to be set. "
                "Blob is the mandatory ingestion source in production."
            )

        # In production, INPUT_SOURCE_PATH should not be used for ingestion
        # (it will only be used if explicitly passed to run_pipeline)
        # This ensures no silent fallback to local files

    return RuntimeConfig(
        app_env=app_env,
        app_version=app_version,
        port=port,
        upload_access_code=upload_access_code,
        persistence_mode=persistence_mode,
        storage_path=storage_path,
        log_level=log_level,
        allow_local_fallback=allow_local_fallback,
        blob_account=blob_account,
        blob_container=blob_container,
        blob_path=blob_path,
        api_base_url=api_base_url,
        enable_pipeline=enable_pipeline,
        input_source_path=input_source_path,
        pipeline_summary_path=pipeline_summary_path,
        azure_storage_connection_string=azure_storage_connection_string,
    )
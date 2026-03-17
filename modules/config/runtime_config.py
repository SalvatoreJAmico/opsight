import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RuntimeConfig:
    app_env: str
    app_version: str
    port: int
    upload_access_code: str
    persistence_mode: str
    storage_path: str
    log_level: str
    blob_account: Optional[str]
    blob_container: Optional[str]
    blob_path: Optional[str]
    api_base_url: Optional[str]
    enable_pipeline: bool
    allow_local_fallback: bool
    input_source_path: Optional[str]


def get_env(name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_app_env(raw_value: str) -> str:
    app_env = raw_value.strip().lower()
    if app_env in {"development", "local"}:
        return "dev"
    if app_env in {"production"}:
        return "prod"
    return app_env


def load_runtime_config() -> RuntimeConfig:
    app_env = _normalize_app_env(get_env("APP_ENV"))

    app_version = get_env("APP_VERSION")
    port_raw = get_env("PORT")
    upload_access_code = get_env("UPLOAD_ACCESS_CODE")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError("Environment variable PORT must be an integer") from exc

    persistence_mode = get_env("PERSISTENCE_MODE")
    storage_path = get_env("STORAGE_PATH")
    log_level = get_env("LOG_LEVEL")

    blob_account = get_env("BLOB_ACCOUNT", required=False, default=None)
    blob_container = get_env("BLOB_CONTAINER", required=False, default=None)
    blob_path = get_env("BLOB_PATH", required=False, default=None)
    api_base_url = get_env("API_BASE_URL", required=False, default=None)
    input_source_path = get_env("INPUT_SOURCE_PATH", required=False, default=None)

    enable_pipeline = _to_bool(get_env("ENABLE_PIPELINE", required=False, default="true"), default=True)
    allow_local_fallback = _to_bool(
        get_env("ALLOW_LOCAL_FALLBACK", required=False, default="true"),
        default=True,
    )

    if app_env == "prod":
        blob_account = get_env("BLOB_ACCOUNT")
        blob_container = get_env("BLOB_CONTAINER")
        if allow_local_fallback:
            raise RuntimeError("Local fallback is not allowed in production")

    return RuntimeConfig(
        app_env=app_env,
        app_version=app_version,
        port=port,
        upload_access_code=upload_access_code,
        persistence_mode=persistence_mode,
        storage_path=storage_path,
        log_level=log_level,
        blob_account=blob_account,
        blob_container=blob_container,
        blob_path=blob_path,
        api_base_url=api_base_url,
        enable_pipeline=enable_pipeline,
        allow_local_fallback=allow_local_fallback,
        input_source_path=input_source_path,
    )

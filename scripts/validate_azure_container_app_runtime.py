from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import modules.config.runtime_config as runtime_config_module
from modules.config.runtime_config import load_runtime_config


DEFAULT_ENV_FILE = PROJECT_ROOT / "configs" / "production.env"
PLACEHOLDER_VALUES = {"", "replace-me", "changeme", "your-value-here"}

REQUIRED_RUNTIME_ENV_VARS = (
    "APP_ENV",
    "APP_VERSION",
    "PORT",
    "PERSISTENCE_MODE",
    "STORAGE_PATH",
    "LOG_LEVEL",
    "ALLOW_LOCAL_FALLBACK",
    "BLOB_ACCOUNT",
    "BLOB_CONTAINER",
    "BLOB_PATH",
    "PIPELINE_SUMMARY_PATH",
)

REQUIRED_RUNTIME_SECRETS = (
    "UPLOAD_ACCESS_CODE",
    "AZURE_STORAGE_CONNECTION_STRING",
)

MANAGED_KEYS = REQUIRED_RUNTIME_ENV_VARS + REQUIRED_RUNTIME_SECRETS + (
    "API_BASE_URL",
    "ENABLE_PIPELINE",
    "INPUT_SOURCE_PATH",
    "CORS_ALLOWED_ORIGINS",
)


def parse_env_file(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_file.exists():
        return values

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


@contextmanager
def merged_environment(env_file: Path | None = None):
    previous = os.environ.copy()
    try:
        if env_file is not None:
            for key in MANAGED_KEYS:
                os.environ.pop(key, None)
            for key, value in parse_env_file(env_file).items():
                os.environ[key] = value
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)


def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in PLACEHOLDER_VALUES


def validate_runtime_secrets() -> list[str]:
    failures: list[str] = []

    upload_access_code = os.getenv("UPLOAD_ACCESS_CODE")
    if _is_placeholder(upload_access_code):
        failures.append(
            "UPLOAD_ACCESS_CODE must be set to a non-placeholder runtime secret in Azure Container Apps."
        )

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if _is_placeholder(connection_string):
        failures.append(
            "AZURE_STORAGE_CONNECTION_STRING must be present as an Azure Container Apps secret for the current Blob auth method."
        )

    return failures


def build_summary() -> str:
    summary_lines = [
        "Validated Azure Container Apps runtime contract:",
        f"- APP_ENV={os.getenv('APP_ENV', '')}",
        f"- APP_VERSION={os.getenv('APP_VERSION', '')}",
        f"- API_BASE_URL={os.getenv('API_BASE_URL', '')}",
        f"- BLOB_ACCOUNT={os.getenv('BLOB_ACCOUNT', '')}",
        f"- BLOB_CONTAINER={os.getenv('BLOB_CONTAINER', '')}",
        f"- BLOB_PATH={os.getenv('BLOB_PATH', '')}",
        f"- CORS_ALLOWED_ORIGINS={'set' if os.getenv('CORS_ALLOWED_ORIGINS') else 'not-set'}",
        f"- Required secrets present: {', '.join(key for key in REQUIRED_RUNTIME_SECRETS if not _is_placeholder(os.getenv(key))) or 'none'}",
    ]
    return "\n".join(summary_lines)


def validate_runtime_contract(env_file: Path | None = None) -> tuple[bool, list[str], str]:
    failures: list[str] = []
    disabled_local_env_path = PROJECT_ROOT / ".env.runtime-validation.disabled"

    with merged_environment(env_file):
        with patch.object(runtime_config_module, "LOCAL_ENV_PATH", disabled_local_env_path):
            try:
                load_runtime_config()
            except RuntimeError as exc:
                failures.append(str(exc))

        for key in REQUIRED_RUNTIME_ENV_VARS:
            if _is_placeholder(os.getenv(key)):
                failures.append(f"{key} must be populated for Azure Container Apps runtime validation.")

        failures.extend(validate_runtime_secrets())
        summary = build_summary()

    deduped_failures = list(dict.fromkeys(failures))
    return not deduped_failures, deduped_failures, summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Azure Container Apps runtime configuration expected by Opsight production deployment."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional env file to merge into the current process environment before validation.",
    )
    args = parser.parse_args()

    env_file = args.env_file if args.env_file else None
    is_valid, failures, summary = validate_runtime_contract(env_file)

    print(summary)
    if is_valid:
        print("Azure Container Apps runtime validation passed.")
        return 0

    print("Azure Container Apps runtime validation failed:")
    for failure in failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
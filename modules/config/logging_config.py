import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter for container-friendly structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "stage"):
            payload["stage"] = record.stage

        if hasattr(record, "event"):
            payload["event"] = record.event

        for key in (
            "service",
            "method",
            "path",
            "status_code",
            "runtime_ms",
            "records_ingested",
            "records_valid",
            "records_invalid",
            "records_persisted",
            "runtime_seconds",
            "failed_stage",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def setup_logging(service_name: str = "opsight") -> None:
    """Configure root logging once for all modules."""
    root_logger = logging.getLogger()
    if getattr(root_logger, "_opsight_configured", False):
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = JsonFormatter()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    handlers = [stream_handler]

    if _to_bool(os.getenv("LOG_TO_FILE", "false")):
        file_path = Path(os.getenv("LOG_FILE", "logs/pipeline_run.log"))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger.setLevel(level)
    root_logger.handlers = handlers
    root_logger._opsight_configured = True

    logging.getLogger(service_name).info(
        "Logging configured",
        extra={
            "event": "logging_configured",
            "service": service_name,
        },
    )
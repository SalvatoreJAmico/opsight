import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request

from modules.config.runtime_config import load_runtime_config

logger = logging.getLogger("opsight.api")


def validate_access_code(submitted_code: Optional[str], expected_code: str) -> bool:
    if not submitted_code:
        return False
    return submitted_code == expected_code


async def _extract_access_code(request: Request, payload: Optional[dict]) -> Optional[str]:
    header_code = (
        request.headers.get("x-upload-access-code")
        or request.headers.get("x-access-code")
        or request.headers.get("upload-access-code")
    )
    if header_code:
        return header_code

    if isinstance(payload, dict):
        body_code = payload.get("access_code")
        if isinstance(body_code, str) and body_code.strip():
            return body_code

    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            form = await request.form()
        except Exception:
            form = None

        if form is not None:
            form_code = form.get("access_code")
            if isinstance(form_code, str) and form_code.strip():
                return form_code

    return None


async def require_upload_access_code(request: Request, payload: Optional[dict]) -> None:
    expected_code = load_runtime_config().upload_access_code
    submitted_code = await _extract_access_code(request, payload)
    is_valid = validate_access_code(submitted_code=submitted_code, expected_code=expected_code)

    route = request.url.path
    client_ip = request.client.host if request.client else None
    logger.info(
        "Protected endpoint access attempt",
        extra={
            "event": "protected_access_attempt",
            "route": route,
            "access_code_valid": is_valid,
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid or missing upload access code")
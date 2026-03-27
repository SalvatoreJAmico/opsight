# Opsight Security Update List (V2)

Date: 2026-03-27
Scope: Repository scan for backend, frontend, config, deployment, and runtime security controls.

## Priority Summary

- P0 (immediate): 3 items
- P1 (next sprint): 6 items
- P2 (hardening): 6 items

## P0 - Immediate

1. Rotate exposed Azure Storage key and purge local secret use
- Why: A real storage account key exists in local `.env`; this is credential exposure risk.
- Evidence: `.env` contains `AZURE_STORAGE_CONNECTION_STRING` with `AccountKey=...`.
- V2 action:
  - Rotate storage account keys now.
  - Replace local value with placeholder.
  - Keep real secret only in Azure runtime secrets (or remove entirely when managed identity is complete).
- Acceptance:
  - Local `.env` has no live cloud secrets.
  - Runtime still passes deployment validation.

2. Protect unauthenticated pipeline trigger endpoint
- Why: `POST /pipeline/trigger` does not require access code or auth and can execute expensive processing.
- Evidence: `modules/api/routes/ingest.py` comment indicates access code was removed for this route.
- V2 action:
  - Require authenticated identity (preferred) or at minimum protect with server-side secret/header and role checks.
  - Add rate limiting for this endpoint.
- Acceptance:
  - Anonymous requests to `/pipeline/trigger` are rejected in production.

3. Remove internal error detail leakage from API responses
- Why: Several handlers return raw exception strings to clients.
- Evidence:
  - `modules/api/errors.py` returns `detail: str(exc)` for unhandled exceptions.
  - `modules/api/routes/ingest.py` returns `Pipeline failure: {str(exc)}`.
  - `modules/api/app.py` chart endpoints return `detail=str(exc)`.
- V2 action:
  - Return generic error messages externally.
  - Keep detailed exception data in structured logs only.
  - Introduce stable error codes.
- Acceptance:
  - No stack/internal message content is exposed in production API responses.

## P1 - Next Sprint

4. Replace upload access code model with real API authN/authZ
- Why: Shared static access code is weak and difficult to rotate/audit.
- Evidence: `modules/api/access_control.py` validates equality against one runtime value.
- V2 action:
  - Add JWT-based auth (or Azure AD / Entra ID) for protected operations.
  - Use route-level authorization scopes/roles.
  - Keep a transitional feature flag if needed.
- Acceptance:
  - Sensitive routes require identity token and role check.

5. Use constant-time secret comparison
- Why: Plain string equality can introduce timing side-channel risk.
- Evidence: `validate_access_code` uses `submitted_code == expected_code`.
- V2 action:
  - Use `hmac.compare_digest()` for secret comparisons.
- Acceptance:
  - Access code compare path uses constant-time compare.

6. Add endpoint-level authorization for state and data operations
- Why: `/session/reset` and entity/status data endpoints are currently open.
- Evidence:
  - `modules/api/routes/status.py` exposes reset endpoint without auth.
  - `modules/api/routes/entities.py` exposes entity reads without auth.
- V2 action:
  - Require authenticated role for reset/admin operations.
  - Define read scopes for entity/status endpoints.
- Acceptance:
  - Unauthorized users cannot reset or read protected data.

7. Enforce strict input constraints for ingestion source paths
- Why: API accepts `source_path`; this can be abused for unauthorized file probing in local mode.
- Evidence: `modules/api/routes/ingest.py` accepts payload dict and passes `source_path` into pipeline path logic.
- V2 action:
  - In production, disallow arbitrary `source_path` input.
  - Allow only dataset IDs or approved blob prefixes.
  - Add schema validation for payload size and format.
- Acceptance:
  - API rejects path-style ingestion input in production.

8. Add request throttling and body size limits
- Why: Pipeline and chart endpoints can be expensive and are vulnerable to abuse.
- Evidence: No rate limiting middleware currently present.
- V2 action:
  - Add IP/token-based rate limits.
  - Set max request body size and timeout policy.
- Acceptance:
  - Load tests show abuse traffic is throttled.

9. Tighten CORS policy defaults for production
- Why: Current config allows all methods/headers whenever origins are set; weak defaults increase attack surface.
- Evidence: `modules/api/app.py` uses `allow_methods=["*"]`, `allow_headers=["*"]`.
- V2 action:
  - Restrict to required methods/headers.
  - Fail startup in production if `CORS_ALLOWED_ORIGINS` is empty.
- Acceptance:
  - Production CORS is explicit and minimal.

## P2 - Hardening

10. Harden container runtime
- Why: Current Dockerfile runs as root and lacks explicit healthcheck.
- Evidence: `Dockerfile` has no `USER` and no `HEALTHCHECK`.
- V2 action:
  - Create non-root user and run app under it.
  - Add healthcheck endpoint probe.
  - Consider read-only root FS + dropped Linux capabilities in runtime config.
- Acceptance:
  - Container passes baseline hardening checklist.

11. Pin and govern dependency versions
- Why: `requirements.txt` uses broad `>=` ranges, reducing reproducibility and patch governance.
- Evidence: `requirements.txt` entries are unpinned minimums.
- V2 action:
  - Use pinned lockfile strategy (`pip-compile` or equivalent).
  - Establish monthly dependency update window.
- Acceptance:
  - Deterministic installs and tracked security patch cadence.

12. Add automated SCA and secret scanning in CI
- Why: No explicit security scanning workflow found in CI.
- Evidence: workflows are deployment-focused.
- V2 action:
  - Add dependency vulnerability scan (e.g., `pip-audit`/`safety`).
  - Add secret scan (e.g., gitleaks) on PR and main.
- Acceptance:
  - CI fails on high/critical findings.

13. Pin GitHub Actions by commit SHA
- Why: Tag-based action references can introduce supply-chain drift.
- Evidence: workflows reference `@v*` tags.
- V2 action:
  - Pin critical actions to trusted SHAs.
- Acceptance:
  - All third-party actions pinned and periodically reviewed.

14. Add security headers middleware
- Why: No explicit hardening headers in API layer.
- V2 action:
  - Add headers: `X-Content-Type-Options`, `X-Frame-Options`, strict `Referrer-Policy`, `Cache-Control` (sensitive routes), and CSP where applicable.
- Acceptance:
  - Security header tests pass in API integration suite.

15. Improve auditability for security events
- Why: Logging is structured, but security events can be expanded for incident response.
- V2 action:
  - Add event IDs and outcomes for auth failures, throttling, and admin actions.
  - Ensure no secrets are ever logged.
- Acceptance:
  - Security events are queryable and complete in production logs.

## Proposed V2 Delivery Plan

Phase A (Week 1)
- Complete P0 items: key rotation, endpoint protection decision, error sanitization.

Phase B (Weeks 2-3)
- Complete P1 authN/authZ + ingestion constraints + throttling + CORS tightening.

Phase C (Week 4)
- Complete P2 hardening and CI scanning rollout.

## Recommended New Tests for V2

- API tests proving protected routes reject anonymous requests.
- Tests proving exception responses are sanitized.
- Tests proving production rejects arbitrary `source_path` payloads.
- Rate-limit tests for `/pipeline/trigger` and `/data`.
- Startup test requiring non-empty production CORS allowlist.
- CI checks for dependency and secret scanning policy.

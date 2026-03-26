# Opsight Configuration

## Environments
Opsight supports environment-based configuration through environment variables.

## Files
- `.env.example` — documented template of required variables
- `configs/production.env` — production-style non-secret settings example

## Required Variables

Required in all environments:

- `APP_ENV` (`dev` or `prod`)
- `APP_VERSION`
- `PORT`
- `UPLOAD_ACCESS_CODE`
- `PERSISTENCE_MODE`
- `STORAGE_PATH`
- `LOG_LEVEL`
- `ALLOW_LOCAL_FALLBACK`
- `PIPELINE_SUMMARY_PATH`

Required only when `APP_ENV=prod`:

- `BLOB_ACCOUNT`
- `BLOB_CONTAINER`
- `BLOB_PATH`

Optional but commonly used:

- `API_BASE_URL`
- `ENABLE_PIPELINE`
- `INPUT_SOURCE_PATH`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER`
- `AZURE_KEY_VAULT_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

## Local vs Production Behavior

- Local (`APP_ENV=dev`): local fallback can be enabled.
- Production (`APP_ENV=prod`): local fallback must be disabled.
- Production requires Blob ingestion settings (`BLOB_ACCOUNT`, `BLOB_CONTAINER`, `BLOB_PATH`).

## Notes
- Never commit real secrets
- Use environment variables for credentials and connection strings
- Production should not rely on development-only defaults
- Bump `APP_VERSION` deliberately for each release deployment (semantic versioning, baseline `1.0.0`)
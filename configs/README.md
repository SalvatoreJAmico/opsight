# Opsight Configuration

## Environments
Opsight supports environment-based configuration through environment variables.

## Files
- `.env.example` — documented template of required variables
- `configs/production.env` — production-style non-secret settings example

## Production Contract

Treat production configuration as three separate buckets:

### 1. Repo-tracked templates

These files document expected keys and safe placeholder values:

- `.env.example`
- `configs/production.env`
- `modules/frontend/.env.example`

These files should never contain real secret values.

### 2. GitHub Actions secrets or variables

These are used by deployment workflows.

Backend deployment workflow currently expects these GitHub secrets:

- `AZURE_CREDENTIALS`
- `AZURE_ACR_LOGIN_SERVER`
- `AZURE_ACR_NAME`
- `AZURE_RESOURCE_GROUP`
- `AZURE_CONTAINER_APP_NAME`

Frontend deployment should use the same pattern: build-time values and deploy tokens belong in GitHub configuration, not in committed files.

### 3. Azure runtime configuration

These values belong on the deployed service itself, for example in Azure Container Apps environment variables or secrets.

Required production runtime values:

- `APP_ENV=prod`
- `APP_VERSION`
- `PORT`
- `UPLOAD_ACCESS_CODE`
- `PERSISTENCE_MODE`
- `STORAGE_PATH`
- `LOG_LEVEL`
- `ALLOW_LOCAL_FALLBACK=false`
- `PIPELINE_SUMMARY_PATH`
- `BLOB_ACCOUNT`
- `BLOB_CONTAINER`
- `BLOB_PATH`

Optional runtime values:

- `API_BASE_URL`
- `ENABLE_PIPELINE`
- `INPUT_SOURCE_PATH`
- `LOG_TO_FILE`
- `LOG_FILE`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER`
- `AZURE_KEY_VAULT_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

If `AZURE_STORAGE_CONNECTION_STRING` is used, treat it as a secret.

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

## Frontend Production Values

For a deployed frontend build, define production frontend values outside source control.

Most important values:

- `VITE_CLOUD_API_URL` or `VITE_API_BASE_URL`
- any deploy token or platform-specific credential required by the frontend host

These values should be supplied through deployment settings rather than committed files.

## Notes
- Never commit real secrets
- Use environment variables for credentials and connection strings
- Production should not rely on development-only defaults
- Bump `APP_VERSION` deliberately for each release deployment (semantic versioning, baseline `1.0.0`)
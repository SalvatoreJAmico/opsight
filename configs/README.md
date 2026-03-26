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

Frontend deployment workflow currently expects:

- GitHub secret `AZURE_STATIC_WEB_APPS_API_TOKEN`
- GitHub repository variable `VITE_CLOUD_API_URL`
- optional GitHub repository variables `VITE_API_BASE_URL` and `VITE_LOCAL_API_URL`

### 3. Azure runtime configuration

These values belong on the deployed service itself, for example in Azure Container Apps environment variables or secrets.

For the current deployment target, the runtime host is Azure Container Apps `opsight-api` in resource group `rg-opsight-dev` in subscription `Amico-DevLab`.

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
- `CORS_ALLOWED_ORIGINS`
- `LOG_TO_FILE`
- `LOG_FILE`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER`
- `AZURE_KEY_VAULT_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

If `AZURE_STORAGE_CONNECTION_STRING` is used, treat it as a secret.

The current production Blob authentication plan uses a connection string, so `AZURE_STORAGE_CONNECTION_STRING` should be present as an Azure Container Apps secret for runtime validation.

`CORS_ALLOWED_ORIGINS` is not a secret. It should be set in deployment configuration when the frontend is hosted on a different origin from the API.

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

## Hosted Persistence Scope (Current)

- Hosted deployment currently runs with `PERSISTENCE_MODE=json`.
- This persistence mode is accepted for demo and portfolio deployment scope.
- Data can be reset when container instances are replaced or restarted.
- Durable persistence migration is a follow-up architecture item, not a blocker for current live deployment.

## Frontend Production Values

For a deployed frontend build, define production frontend values outside source control.

Most important values:

- `VITE_CLOUD_API_URL` or `VITE_API_BASE_URL`
- any deploy token or platform-specific credential required by the frontend host

For the Azure Static Web Apps workflow in this repo, keep the deploy token in `AZURE_STATIC_WEB_APPS_API_TOKEN` and set frontend URLs through GitHub repository variables.

When the frontend and API are hosted on different origins, the backend must also define `CORS_ALLOWED_ORIGINS` to include the deployed frontend URL.

These values should be supplied through deployment settings rather than committed files.

## Notes
- Never commit real secrets
- Use environment variables for credentials and connection strings
- Production should not rely on development-only defaults
- Bump `APP_VERSION` deliberately for each release deployment (semantic versioning, baseline `1.0.0`)

## Runtime Validation

Use the repo validator before or after setting Azure Container Apps configuration:

```powershell
./validate_opsight_runtime.bat
```

That command validates the current production contract, including the current Blob connection-string requirement, without printing secret values.
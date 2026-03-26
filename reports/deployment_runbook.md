# Opsight Deployment Runbook And Rollback Guide

## Live URLs

- Frontend URL: https://agreeable-cliff-08bf3bd0f.2.azurestaticapps.net
- API URL: https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io

## Scope

This runbook covers:

- Azure Static Web Apps frontend deployment
- Azure Container Apps backend runtime validation
- Post-deploy smoke validation
- Rollback for frontend and backend

## Prerequisites

- Azure subscription: `Amico-DevLab`
- Resource group: `rg-opsight-dev`
- Region: `East US`
- GitHub repo secrets configured:
  - `AZURE_CREDENTIALS`
  - `AZURE_ACR_LOGIN_SERVER`
  - `AZURE_ACR_NAME`
  - `AZURE_RESOURCE_GROUP`
  - `AZURE_CONTAINER_APP_NAME`
  - `AZURE_STATIC_WEB_APPS_API_TOKEN`
- GitHub repo variable configured:
  - `VITE_CLOUD_API_URL=https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io`
- Azure Container App runtime secrets configured:
  - `UPLOAD_ACCESS_CODE`
  - `AZURE_STORAGE_CONNECTION_STRING`
- Azure Container App runtime environment values configured:
  - `APP_ENV=prod`
  - `APP_VERSION` (release value)
  - `BLOB_ACCOUNT=stopsightdev`
  - `BLOB_CONTAINER=opsight-raw`
  - `BLOB_PATH=csv/Sample - Superstore.csv`
  - `CORS_ALLOWED_ORIGINS=https://agreeable-cliff-08bf3bd0f.2.azurestaticapps.net`

## Persistence Decision (PS-166)

- Current hosted persistence mode is `PERSISTENCE_MODE=json` with local JSON file storage.
- This is accepted for demo and portfolio deployment scope.
- Data can be lost on container restart or replacement.
- Durable storage migration remains a future enhancement and is out of this deployment gate.

## Deployment Steps

1. Deploy backend image to Azure Container Apps via `.github/workflows/deploy-api.yml`.
2. Verify API health endpoint is reachable.
3. Deploy frontend via `.github/workflows/deploy-frontend.yml`.
4. Confirm frontend URL is reachable.
5. Confirm backend `CORS_ALLOWED_ORIGINS` includes the frontend URL.

## Verification Steps (Ordered)

1. Runtime contract check:

```powershell
./validate_opsight_runtime.bat
```

2. Live smoke suite check:

```powershell
./run_live_smoke_tests.bat https://agreeable-cliff-08bf3bd0f.2.azurestaticapps.net https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io
```

3. Confirm successful checks include:
   - frontend load
   - API health
   - pipeline trigger with blob dataset
   - charts overview endpoint
   - model execution endpoint
   - frontend production API wiring (no dev proxy dependency)

## Rollback Guide

### Frontend rollback (Azure Static Web Apps)

1. Open Azure Static Web Apps deployment history.
2. Select the previous known-good deployment.
3. Promote/restore that deployment.
4. Re-run live smoke suite to confirm recovery.

### Backend rollback (Azure Container Apps)

1. Open Azure Container App revision history for `opsight-api`.
2. Activate the previous known-good revision.
3. Confirm runtime secrets and env values remain intact.
4. Validate `GET /health` and rerun smoke tests.

### Emergency fallback

If both UI and API latest deployments are faulty:

1. Roll back backend revision first.
2. Roll back frontend deployment second.
3. Re-run runtime validator and smoke suite.
4. Post incident note in deployment issues with failing revision IDs and restoration timestamps.
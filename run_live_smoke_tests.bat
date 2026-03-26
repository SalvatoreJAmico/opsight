@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage: run_live_smoke_tests.bat ^<frontend-url^> ^<api-url^> [dataset-id]
  exit /b 1
)

if "%~2"=="" (
  echo Usage: run_live_smoke_tests.bat ^<frontend-url^> ^<api-url^> [dataset-id]
  exit /b 1
)

set "FRONTEND_URL=%~1"
set "API_URL=%~2"
set "DATASET_ID=%~3"
if "%DATASET_ID%"=="" set "DATASET_ID=sales_csv"

".venv\Scripts\python.exe" scripts\smoke_test_live_deployment.py --frontend-url "%FRONTEND_URL%" --api-url "%API_URL%" --dataset-id "%DATASET_ID%"
exit /b %errorlevel%
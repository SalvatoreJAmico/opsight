@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Missing virtual environment Python at .venv\Scripts\python.exe
  exit /b 1
)

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=configs\production.env"

echo Validating Opsight Azure Container Apps runtime using %ENV_FILE%...
".venv\Scripts\python.exe" scripts\validate_azure_container_app_runtime.py --env-file "%ENV_FILE%"
exit /b %errorlevel%
@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========== Starting Opsight (Production Mode) ==========
echo.

set "ENV_FILE=configs\production.env"
if not exist "%ENV_FILE%" (
  echo [ERROR] Missing %ENV_FILE%
  exit /b 1
)

echo [0/4] Loading production environment from %ENV_FILE%...
for /f "usebackq tokens=1* delims==" %%A in ("%ENV_FILE%") do (
  if not "%%A"=="" set "%%A=%%B"
)

if "%PORT%"=="" set "PORT=8000"
if "%PIPELINE_SUMMARY_PATH%"=="" set "PIPELINE_SUMMARY_PATH=reports/pipeline_run_summary.json"

REM Frontend production build has no API target switch, so point cloud/local to local backend for easy local demos.
set "VITE_LOCAL_API_URL=http://127.0.0.1:%PORT%"
set "VITE_CLOUD_API_URL=http://127.0.0.1:%PORT%"

echo [1/4] Starting backend API (uvicorn, production flags)...
start "Opsight Backend (Prod)" cmd /c "cd /d ""%~dp0"" && .venv\Scripts\uvicorn modules.api.app:app --host 127.0.0.1 --port %PORT%"

echo [2/4] Building frontend (vite build)...
call cmd /c "cd /d ""%~dp0modules\frontend"" && npm run build"
if errorlevel 1 (
  echo [ERROR] Frontend build failed.
  exit /b 1
)

echo [3/4] Starting frontend preview server...
start "Opsight Frontend (Prod Preview)" cmd /c "cd /d ""%~dp0modules\frontend"" && npm run preview -- --host 127.0.0.1 --port 4173"

echo [4/4] Waiting for services to start (12 seconds)...
timeout /t 12 >nul

echo.
echo Opening Opsight Production Preview in browser...
start "" "http://127.0.0.1:4173"

echo.
echo ========== Opsight Production Preview Started ==========
echo Backend API:   http://127.0.0.1:%PORT%
echo Frontend UI:   http://127.0.0.1:4173
echo.
echo To stop both servers: run stop_opsight.bat
echo.
endlocal

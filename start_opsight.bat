@echo off
cd /d "%~dp0"
setlocal

echo.
echo ========== Starting Opsight ==========
echo.

REM Start backend API server
echo [1/3] Starting backend API (uvicorn)...
start "Opsight Backend" .venv\Scripts\uvicorn modules.api.app:app --reload

REM Wait for backend API readiness before launching frontend
echo [2/3] Waiting for backend health check...
set API_READY=0
for /L %%I in (1,1,25) do (
	powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
	if not errorlevel 1 (
		set API_READY=1
		goto :api_ready
	)
	timeout /t 1 >nul
)

:api_ready
if "%API_READY%"=="0" (
	echo.
	echo Backend API did not become healthy in time.
	echo Frontend startup skipped to avoid proxy errors.
	echo Check backend logs, then rerun start_opsight.bat.
	echo.
	exit /b 1
)

REM Start frontend dev server
echo [3/3] Starting frontend dev server (npm)...
start "Opsight Frontend" cmd /c "cd /d ""%~dp0modules\frontend"" && npm run dev"

REM Wait for frontend to initialize
echo Waiting for frontend to start (6 seconds)...
timeout /t 6 >nul

REM Wait for services to start
echo Finalizing startup (2 seconds)...
timeout /t 2 >nul

echo.
echo Opening Opsight in browser...
timeout /t 2 >nul
start "" "http://localhost:5173"

echo.
echo ========== Opsight Started ==========
echo Backend API:   http://localhost:8000
echo Frontend UI:   http://localhost:5173
echo.
echo To stop: Run stop_opsight.bat
echo.
endlocal
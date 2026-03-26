@echo off
cd /d "%~dp0"

echo.
echo ========== Starting Opsight ==========
echo.

REM Start backend API server
echo [1/3] Starting backend API (uvicorn)...
start "Opsight Backend" .venv\Scripts\uvicorn modules.api.app:app --reload

REM Start frontend dev server
echo [2/3] Starting frontend dev server (npm)...
start "Opsight Frontend" cmd /c "cd /d ""%~dp0modules\frontend"" && npm run dev"

REM Wait for services to start
echo [3/3] Waiting for services to start (12 seconds)...
timeout /t 12 >nul

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
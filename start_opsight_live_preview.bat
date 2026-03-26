@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========== Starting Opsight Live Proxy Mode ==========
echo.

set "LIVE_API_URL=https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io"

echo [1/3] Configuring Vite proxy to live API: %LIVE_API_URL%
set "VITE_API_PROXY_TARGET=%LIVE_API_URL%"
set "VITE_API_PROXY_TARGET_LOCAL=%LIVE_API_URL%"

echo [2/3] Starting frontend dev server with live proxy...
start "Opsight Frontend (Live Proxy)" cmd /c "cd /d ""%~dp0modules\frontend"" && npx vite --host 127.0.0.1 --port 4174"

echo [3/3] Waiting for preview server to start (6 seconds)...
timeout /t 6 >nul

echo.
echo Opening Live Proxy UI in browser...
start "" "http://127.0.0.1:4174"

echo.
echo ========== Opsight Live Proxy Started ==========
echo Frontend UI:   http://127.0.0.1:4174
echo Live API:      %LIVE_API_URL%
echo Mode:          Vite dev + proxy (/api-local and /api-cloud)
echo.
echo To stop preview: run stop_opsight.bat
echo.
endlocal

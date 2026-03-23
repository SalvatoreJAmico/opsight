@echo off
cd /d "%~dp0"

start /b "" .venv\Scripts\uvicorn modules.api.app:app --reload
start /b "" cmd /c "cd /d ""%~dp0modules\frontend"" && npm run dev"

timeout /t 4 >nul
start "" "http://localhost:5173"
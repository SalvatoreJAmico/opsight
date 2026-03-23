@echo off
taskkill /f /im uvicorn.exe >nul 2>nul
taskkill /f /im node.exe >nul 2>nul
echo Opsight processes stopped.
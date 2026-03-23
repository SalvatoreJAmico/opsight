@echo off
call "%~dp0stop_opsight.bat"
timeout /t 2 >nul
call "%~dp0start_opsight.bat"
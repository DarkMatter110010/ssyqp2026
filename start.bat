@echo off
chcp 65001 >nul
taskkill /F /IM nginx.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano -p tcp ^| findstr /r /c:":5050 .*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
start "益起跑-Flask后端" /d "%~dp0server" "%~dp0.venv\Scripts\python.exe" main.py
start "益起跑-Nginx" /b /d "%~dp0server\nginx" "%~dp0server\nginx\nginx.exe"

cd /d %~dp0
start "" "https://127.100.10.1:7443"
start "" "%~dp0.venv\Scripts\python.exe" "%~dp0data_client\db_client.py"
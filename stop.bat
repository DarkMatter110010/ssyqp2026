@echo off
chcp 65001 >nul
taskkill /F /IM nginx.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
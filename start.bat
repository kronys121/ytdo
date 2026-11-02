@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title YouTube Downloader

if not exist ".venv\Scripts\python.exe" (
    echo Зависимости не установлены, запускаю install.bat ...
    call install.bat
    if not exist ".venv\Scripts\python.exe" exit /b 1
)

set PYTHONUTF8=1
".venv\Scripts\python.exe" ytdo.py
pause

@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title YouTube Downloader - установка

echo ==================================================
echo  Установка / обновление зависимостей
echo ==================================================

set "PY="
where py >nul 2>&1 && py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && python -c "import sys" >nul 2>&1 && set "PY=python"
)

if not defined PY (
    echo Python не найден. Пробую установить через winget...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo winget недоступен. Установите Python 3.10+ вручную с https://www.python.org/downloads/
        echo При установке отметьте галочку "Add python.exe to PATH".
        pause
        exit /b 1
    )
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    echo.
    echo Python установлен. Закройте это окно и запустите install.bat ещё раз.
    pause
    exit /b 0
)

echo Использую: %PY%

if not exist ".venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
)

echo Обновляю pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo Устанавливаю yt-dlp, deno и ffmpeg...
".venv\Scripts\python.exe" -m pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo Ошибка установки пакетов. Проверьте интернет и попробуйте снова.
    pause
    exit /b 1
)

echo.
echo Готово. Теперь запускайте start.bat
pause

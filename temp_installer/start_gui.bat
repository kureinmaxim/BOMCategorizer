@echo off
REM ========================================
REM BOM Categorizer GUI launcher
REM Запуск графического интерфейса
REM ========================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Запустите сначала: python -m venv .venv
    echo Затем: .venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

echo Запуск BOM Categorizer GUI...
start "" .venv\Scripts\pythonw.exe app.py


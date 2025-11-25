@echo off
REM ========================================
REM BOM Categorizer CLI wrapper
REM Использование: split_bom.bat [опции]
REM ========================================

cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Запустите сначала: python -m venv .venv
    echo Затем: .venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

.venv\Scripts\python.exe split_bom.py %*


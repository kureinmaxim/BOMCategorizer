@echo off
chcp 65001 >nul
REM Быстрый просмотр статистики базы данных

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe manage_database.py --stats
) else if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage_database.py --stats
) else (
    echo Ошибка: виртуальное окружение не найдено!
    pause
    exit /b 1
)

echo.
pause


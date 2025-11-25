@echo off
chcp 65001 >nul
REM Быстрое создание резервной копии базы данных

cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe manage_database.py --backup
) else if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage_database.py --backup
) else (
    echo Ошибка: виртуальное окружение не найдено!
    pause
    exit /b 1
)

echo.
pause


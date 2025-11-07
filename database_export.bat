@echo off
chcp 65001 >nul
REM Экспорт базы данных в Excel

cd /d "%~dp0"

REM Генерируем имя файла с текущей датой
for /f "tokens=1-3 delims=." %%a in ('echo %date%') do (
    set DATE_STR=%%c%%b%%a
)
set OUTPUT_FILE=component_database_%DATE_STR%.xlsx

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe manage_database.py --export "%OUTPUT_FILE%"
) else if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage_database.py --export "%OUTPUT_FILE%"
) else (
    echo Ошибка: виртуальное окружение не найдено!
    pause
    exit /b 1
)

echo.
echo Файл сохранен: %OUTPUT_FILE%
echo Вы можете открыть его в Excel для редактирования.
echo.
pause


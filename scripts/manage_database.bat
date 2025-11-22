@echo off
chcp 65001 >nul
REM Запуск инструмента управления базой данных

REM Переходим в папку со скриптом
cd /d "%~dp0"

REM Проверяем наличие виртуального окружения
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    echo Ошибка: виртуальное окружение не найдено!
    echo Пожалуйста, сначала установите зависимости.
    pause
    exit /b 1
)

REM Если нет аргументов - показываем справку
if "%1"=="" (
    echo.
    echo ========================================
    echo   УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ КОМПОНЕНТОВ
    echo ========================================
    echo.
    echo Использование:
    echo   manage_database.bat --stats          Показать статистику
    echo   manage_database.bat --backup         Создать резервную копию
    echo   manage_database.bat --list-backups   Список резервных копий
    echo   manage_database.bat --export FILE    Экспорт в Excel
    echo   manage_database.bat --import FILE    Импорт из Excel
    echo   manage_database.bat --help           Полная справка
    echo.
    echo Примеры:
    echo   manage_database.bat --stats
    echo   manage_database.bat --export database.xlsx
    echo   manage_database.bat --import database.xlsx
    echo.
    pause
    exit /b 0
)

REM Запускаем с переданными аргументами
%PYTHON% manage_database.py %*

REM Пауза только если не было --help
if not "%1"=="--help" (
    echo.
    pause
)


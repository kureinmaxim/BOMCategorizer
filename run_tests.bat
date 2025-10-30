@echo off
REM Скрипт для запуска тестов BOM Categorizer

echo ====================================
echo BOM Categorizer - Test Runner
echo ====================================
echo.

REM Проверяем наличие виртуального окружения
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Виртуальное окружение не найдено!
    echo.
    echo Создайте окружение:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Активируем виртуальное окружение
call .venv\Scripts\activate.bat

REM Проверяем установлен ли pytest
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [WARNING] pytest не установлен. Устанавливаю...
    pip install pytest pytest-html pytest-cov
    echo.
)

REM Запускаем тесты с параметрами
if "%1"=="" (
    echo Запуск всех тестов...
    python run_tests.py -v
) else if "%1"=="quick" (
    echo Запуск быстрых unit-тестов...
    python run_tests.py --quick -v
) else if "%1"=="integration" (
    echo Запуск интеграционных тестов...
    python run_tests.py --integration -v
) else if "%1"=="coverage" (
    echo Запуск с покрытием кода...
    python run_tests.py --coverage -v
) else (
    echo Запуск тестов с параметром: %*
    python run_tests.py %*
)

echo.
echo ====================================
echo Тестирование завершено
echo ====================================
pause

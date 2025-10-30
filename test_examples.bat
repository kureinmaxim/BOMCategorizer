@echo off
REM Скрипт для тестирования на реальных файлах из example/

echo ====================================
echo BOM Categorizer - Test Examples
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

REM Запускаем тестирование
if "%1"=="" (
    echo Тестирование всех файлов из example/...
    python test_on_examples.py -v
) else (
    echo Тестирование файла: %*
    python test_on_examples.py %* -v
)

echo.
echo ====================================
echo Тестирование завершено
echo ====================================
echo.
echo Результаты в папке: test_output\
pause

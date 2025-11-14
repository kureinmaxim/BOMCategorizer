@echo off
chcp 65001 >nul
title Проверка шрифтов для PDF экспорта

echo ========================================
echo Проверка шрифтов для PDF экспорта
echo ========================================
echo.

REM Активируем виртуальное окружение
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✓ Виртуальное окружение активировано
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✓ Виртуальное окружение активировано
) else (
    echo ⚠ Виртуальное окружение не найдено, используется системный Python
)

echo.
echo Запуск проверки...
echo.

python check_pdf_fonts.py

pause


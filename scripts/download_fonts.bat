@echo off
chcp 65001 >nul
title Скачивание шрифтов DejaVu Sans

echo ========================================
echo Скачивание шрифтов DejaVu Sans
echo ========================================
echo.

REM Переходим в корень проекта
cd /d "%~dp0.."

REM Создаем папку fonts если её нет
if not exist "fonts" (
    mkdir fonts
    echo [+] Создана папка fonts
)

REM Проверяем наличие PowerShell
where powershell >nul 2>&1
if errorlevel 1 (
    echo [!] PowerShell не найден
    echo [!] Пожалуйста, скачайте шрифты вручную с https://dejavu-fonts.github.io/
    pause
    exit /b 1
)

REM Запускаем PowerShell скрипт
echo Запуск скрипта загрузки...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0download_fonts.ps1"

echo.
echo ========================================
echo Нажмите любую клавишу для выхода...
pause >nul

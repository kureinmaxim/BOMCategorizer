@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0.."

:: Create a log file for debugging
echo Launching BOM Categorizer... > debug_log.txt
echo Current directory: %CD% >> debug_log.txt
echo Script location: %~dp0 >> debug_log.txt
echo. >> debug_log.txt

:: Check if virtual environment exists. If not, run setup.
if exist ".venv\Scripts\python.exe" (
    echo Virtual environment found. Skipping setup. >> debug_log.txt
) else (
    echo Virtual environment not found. Starting setup... >> debug_log.txt
    
    cls
    echo ========================================
    echo BOM Categorizer - First Run Setup
    echo ========================================
    echo.
    echo Virtual environment not found. This is normal for the first run.
    echo.
    echo Press any key to install dependencies...
    pause >nul
    
    echo.
    echo Installing dependencies, please wait...
    echo.
    
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0post_install.ps1"
    
    if %errorlevel% neq 0 (
        echo.
        echo ========================================
        echo INSTALLATION FAILED
        echo ========================================
        echo.
        echo Please check install_log.txt for details.
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo ========================================
    echo Installation completed successfully!
    echo ========================================
    echo.
    echo Starting application...
    timeout /t 2 >nul
)

:: Final check before launch
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment still not found after setup! >> debug_log.txt
    echo ERROR: Installation might have failed. Please run repair_install.bat
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ERROR: app.py not found! >> debug_log.txt
    echo ERROR: Main application file app.py is missing.
    pause
    exit /b 1
)

:: Launch application
echo Starting application with python.exe... >> debug_log.txt
.venv\Scripts\python.exe app.py

:: Keep console open to see output/errors
echo.
echo Application closed.
pause

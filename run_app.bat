@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: Create a log file for debugging
echo Launching BOM Categorizer... > debug_log.txt
echo. >> debug_log.txt

if exist ".venv\Scripts\python.exe" (
    echo Found Python in .venv. Checking installed packages... >> debug_log.txt
    echo. >> debug_log.txt
    
    echo ===== VENV PACKAGE LIST ===== >> debug_log.txt
    if exist ".venv\Scripts\pip.exe" (
        call .venv\Scripts\pip.exe list >> debug_log.txt 2>>&1
    ) else if exist ".venv\Scripts\pip3.exe" (
        call .venv\Scripts\pip3.exe list >> debug_log.txt 2>>&1
    ) else (
        call .venv\Scripts\python.exe -m pip list >> debug_log.txt 2>>&1
    )
    echo. >> debug_log.txt
    echo ===== END OF PACKAGE LIST ===== >> debug_log.txt
    echo. >> debug_log.txt
    
    echo Starting app.py, redirecting output to log... >> debug_log.txt
    call .venv\Scripts\python.exe app_qt.py >> debug_log.txt 2>>&1
    echo App execution finished. >> debug_log.txt

) else (
    echo ERROR: Virtual environment not found! >> debug_log.txt
    echo Searched for python.exe in: %~dp0.venv\Scripts\ >> debug_log.txt
    echo. >> debug_log.txt
    echo Attempting to repair installation... >> debug_log.txt
    
    cls
    echo ========================================
    echo BOM Categorizer - First Run Setup
    echo ========================================
    echo.
    echo Virtual environment not found.
    echo.
    echo This is normal for first run or if installation was incomplete.
    echo.
    echo Press any key to install dependencies (requires Python)...
    pause >nul
    
    echo.
    echo Installing dependencies...
    echo Please wait, this may take a few minutes...
    echo.
    
    :: Try to run post_install.ps1
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0post_install.ps1"
    
    if errorlevel 1 (
        echo.
        echo ========================================
        echo Installation FAILED
        echo ========================================
        echo.
        echo Please check:
        echo   1. Python is installed on your system
        echo   2. You have internet connection
        echo   3. Check install_log.txt for details
        echo.
        echo For help, see: %~dp0install_log.txt
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo.
    echo ========================================
    echo Installation completed successfully!
    echo ========================================
    echo.
    echo Starting application...
    timeout /t 2 >nul
    
    :: Now try to start the app
    if exist ".venv\Scripts\python.exe" (
        call .venv\Scripts\python.exe app_qt.py
    ) else (
        echo ERROR: Installation completed but .venv still not found!
        echo Please run repair_install.bat
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo The program has finished executing.
echo ========================================
echo.
echo Debug log: %~dp0debug_log.txt
echo Install log: %~dp0install_log.txt
echo.
echo Press any key to close...
pause >nul

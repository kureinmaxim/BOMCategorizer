@echo off
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
    call .venv\Scripts\python.exe app.py >> debug_log.txt 2>>&1
    echo App execution finished. >> debug_log.txt

) else (
    echo ERROR: Virtual environment not found! Please check installation. >> debug_log.txt
    echo Searched for python.exe in: %~dp0.venv\Scripts\ >> debug_log.txt
)

echo.
echo The program has finished executing.
echo A debug log has been created at: %~dp0debug_log.txt
echo If the app did not start, please check this file for errors.
echo.
echo Press any key to close this window...
pause

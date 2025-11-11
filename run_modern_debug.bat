@echo off
cd /d "C:\Project\BOMCategorizer"
echo ====================================
echo BOM Categorizer Modern Edition
echo Debug Mode (Console visible)
echo ====================================
echo.
echo Project directory: C:\Project\BOMCategorizer
echo Current directory: %CD%
echo Python executable: .\.venv\Scripts\python.exe
echo.
echo Starting application...
echo.
.\.venv\Scripts\python.exe app_qt.py
echo.
echo ====================================
echo Application closed
echo ====================================
pause


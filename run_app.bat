@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe app.py
) else (
    echo Virtual environment not found. Please run post_install.ps1 first.
    pause
)

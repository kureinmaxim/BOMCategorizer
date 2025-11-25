@echo off
:: Batch wrapper for repair_install.ps1
:: This script repairs a failed BOM Categorizer installation

cd /d "%~dp0"

echo ===============================================
echo BOM Categorizer Installation Repair
echo ===============================================
echo.
echo This script will repair your BOM Categorizer installation
echo by installing all required dependencies.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause

powershell.exe -ExecutionPolicy Bypass -File "%~dp0repair_install.ps1"

echo.
echo Repair script completed.
echo Check repair_log.txt for details.
echo.
pause


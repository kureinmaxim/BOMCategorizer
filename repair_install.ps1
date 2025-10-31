# Script to repair BOM Categorizer installation
# Run this script from the installation directory

$ErrorActionPreference = "Stop"
$LogFile = Join-Path $PSScriptRoot "repair_log.txt"
Start-Transcript -Path $LogFile -Force

Write-Host "==============================================="
Write-Host "BOM Categorizer Installation Repair Script"
Write-Host "==============================================="
Write-Host ""

# Change to the script's directory
Set-Location $PSScriptRoot
Write-Host "Working directory: $(Get-Location)"
Write-Host ""

# Check if virtual environment exists
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $VenvPython)) {
    Write-Host "ERROR: Virtual environment not found at: $VenvPython"
    Write-Host "Please run the installer again."
    Stop-Transcript
    Read-Host "Press Enter to exit"
    Exit 1
}

Write-Host "Found virtual environment."
Write-Host "Python: $VenvPython"
Write-Host ""

# Check for offline packages
$OfflinePackagesDir = Join-Path $PSScriptRoot "offline_packages"
if (!(Test-Path $OfflinePackagesDir)) {
    Write-Host "ERROR: offline_packages directory not found!"
    Write-Host "Expected location: $OfflinePackagesDir"
    Stop-Transcript
    Read-Host "Press Enter to exit"
    Exit 1
}

Write-Host "Found offline packages directory."
Write-Host "Packages:"
Get-ChildItem $OfflinePackagesDir -Filter "*.whl" | ForEach-Object {
    Write-Host "  - $($_.Name)"
}
Write-Host ""

# Check for requirements.txt
$RequirementsFile = Join-Path $PSScriptRoot "requirements.txt"
if (!(Test-Path $RequirementsFile)) {
    Write-Host "ERROR: requirements.txt not found!"
    Stop-Transcript
    Read-Host "Press Enter to exit"
    Exit 1
}

Write-Host "Found requirements.txt"
Write-Host "Contents:"
Get-Content $RequirementsFile | ForEach-Object {
    Write-Host "  - $_"
}
Write-Host ""

# Try to use pip
Write-Host "Attempting to install packages..."
Write-Host "Command: python -m pip install --no-index --find-links=offline_packages -r requirements.txt"
Write-Host ""

& $VenvPython -m pip install --no-index --find-links="$OfflinePackagesDir" -r $RequirementsFile

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==============================================="
    Write-Host "SUCCESS! All packages installed successfully."
    Write-Host "==============================================="
    Write-Host ""
    Write-Host "Verifying installation..."
    Write-Host "Installed packages:"
    & $VenvPython -m pip list
    Write-Host ""
    Write-Host "You can now run the application from the Start Menu."
} else {
    Write-Host ""
    Write-Host "==============================================="
    Write-Host "ERROR: Failed to install packages."
    Write-Host "==============================================="
    Write-Host ""
    Write-Host "Please check the log file: $LogFile"
}

Stop-Transcript
Write-Host ""
Read-Host "Press Enter to exit"


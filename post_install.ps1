# Redirect all output to a log file in the script's directory
$LogFile = Join-Path $PSScriptRoot "install_log.txt"
Start-Transcript -Path $LogFile -Force

# CRITICAL: Change to the script's directory
Set-Location $PSScriptRoot
Write-Host "Starting post-install script..."
Write-Host "Log file will be created at: $LogFile"
Write-Host "Script execution directory: $PSScriptRoot"
Write-Host "Current working directory: $(Get-Location)"
Write-Host "System PATH: $($env:PATH)"

# Check if a system-wide python is available
$PythonExe = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $PythonExe) {
    Write-Host "ERROR: Python is not found in the system PATH. Cannot create virtual environment."
    Exit 1
}
Write-Host "Found Python executable at: $($PythonExe.Source)"

Write-Host "Creating virtual environment..."
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$VenvPip = Join-Path $PSScriptRoot ".venv\Scripts\pip.exe"

# Remove old/corrupted virtual environment if it exists but is incomplete
if ((Test-Path ".venv") -and !(Test-Path $VenvPython)) {
    Write-Host "Found incomplete virtual environment. Removing it..."
    Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Create virtual environment if it doesn't exist
if (!(Test-Path $VenvPython)) {
    Write-Host "Creating new virtual environment at: .venv"
    & $PythonExe.Source -m venv .venv --without-pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment."
        Exit 1
    }
    
    # Verify python.exe was created
    if (!(Test-Path $VenvPython)) {
        Write-Host "ERROR: Virtual environment created but python.exe not found at: $VenvPython"
        Exit 1
    }
    Write-Host "Virtual environment created successfully."
} else {
    Write-Host "Virtual environment already exists."
}

Write-Host "Installing dependencies..."

# Ensure pip is installed in the virtual environment
if (!(Test-Path $VenvPip)) {
    Write-Host "pip.exe not found. Installing pip using ensurepip (offline method)..."
    & $VenvPython -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install pip using ensurepip."
        Write-Host "This is a critical error. Python installation may be corrupted."
        Exit 1
    }
    Write-Host "pip installed successfully (offline)."
    
    # Wait a moment for filesystem to sync
    Start-Sleep -Seconds 2
}

# Verify pip is now available - check multiple possible names
Write-Host "Checking for pip executable..."
$VenvScriptsDir = Join-Path $PSScriptRoot ".venv\Scripts"
Write-Host "Scripts directory contents:"
if (Test-Path $VenvScriptsDir) {
    Get-ChildItem $VenvScriptsDir | ForEach-Object { Write-Host "  - $($_.Name)" }
}

# Try to find pip with different names
$PipExecutable = $null
$PossiblePipNames = @("pip.exe", "pip3.exe", "pip3.13.exe")
foreach ($pipName in $PossiblePipNames) {
    $pipPath = Join-Path $VenvScriptsDir $pipName
    if (Test-Path $pipPath) {
        Write-Host "Found pip at: $pipPath"
        $PipExecutable = $pipPath
        break
    }
}

# If still not found, try using python -m pip
if ($null -eq $PipExecutable) {
    Write-Host "No pip.exe found, will use 'python -m pip' instead"
    # Test if python -m pip works
    & $VenvPython -m pip --version
    if ($LASTEXITCODE -eq 0) {
        Write-Host "python -m pip works, using this method"
        $UsePythonModule = $true
    } else {
        Write-Host "ERROR: Cannot find or use pip in virtual environment"
        Exit 1
    }
} else {
    $UsePythonModule = $false
}

# Skip pip upgrade for offline installation

Write-Host "Installing application dependencies from offline packages..."
$OfflinePackagesDir = Join-Path $PSScriptRoot "offline_packages"

if (Test-Path $OfflinePackagesDir) {
    Write-Host "Found offline packages directory. Installing from local files (no internet required)..."
    
    if ($UsePythonModule) {
        & $VenvPython -m pip install --no-index --find-links="$OfflinePackagesDir" -r requirements.txt
    } else {
        & $PipExecutable install --no-index --find-links="$OfflinePackagesDir" -r requirements.txt
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All dependencies installed successfully from offline packages."
    } else {
        Write-Host "ERROR: Failed to install dependencies from offline packages."
        Exit 1
    }
} else {
    Write-Host "WARNING: offline_packages directory not found. This installation requires internet connection."
    Write-Host "Installing from PyPI..."
    
    if ($UsePythonModule) {
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r requirements.txt
    } else {
        & $PipExecutable install --upgrade pip
        & $PipExecutable install -r requirements.txt
    }
}

Write-Host "Installation script finished successfully."
Write-Host "You can launch the app from the Start Menu shortcut."

Stop-Transcript



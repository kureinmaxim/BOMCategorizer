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
$RequirementsFile = Join-Path $PSScriptRoot "requirements.txt"

# Verify requirements.txt exists
if (!(Test-Path $RequirementsFile)) {
    Write-Host "ERROR: requirements.txt not found at: $RequirementsFile"
    Exit 1
}

Write-Host "Requirements file: $RequirementsFile"
Write-Host "Requirements content:"
Get-Content $RequirementsFile | ForEach-Object { Write-Host "  - $_" }

if (Test-Path $OfflinePackagesDir) {
    Write-Host "Found offline packages directory. Installing from local files (no internet required)..."
    Write-Host "Offline packages directory: $OfflinePackagesDir"
    
    # List available packages
    Write-Host "Available offline packages:"
    Get-ChildItem $OfflinePackagesDir -Filter "*.whl" | ForEach-Object { Write-Host "  - $($_.Name)" }
    
    Write-Host "Running pip install command..."
    if ($UsePythonModule) {
        Write-Host "Command: $VenvPython -m pip install --no-index --find-links=$OfflinePackagesDir -r $RequirementsFile"
        & $VenvPython -m pip install --no-index --find-links="$OfflinePackagesDir" -r $RequirementsFile
    } else {
        Write-Host "Command: $PipExecutable install --no-index --find-links=$OfflinePackagesDir -r $RequirementsFile"
        & $PipExecutable install --no-index --find-links="$OfflinePackagesDir" -r $RequirementsFile
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All dependencies installed successfully from offline packages."
        Write-Host ""
        Write-Host "Verifying installed packages:"
        if ($UsePythonModule) {
            & $VenvPython -m pip list
        } else {
            & $PipExecutable list
        }
    } else {
        Write-Host "ERROR: Failed to install dependencies from offline packages."
        Write-Host "Exit code: $LASTEXITCODE"
        Write-Host ""
        Write-Host "You can try to repair the installation by running repair_install.bat"
        Write-Host "from the installation directory: $PSScriptRoot"
        Exit 1
    }
} else {
    Write-Host "WARNING: offline_packages directory not found at: $OfflinePackagesDir"
    Write-Host "This installation requires internet connection."
    Write-Host "Installing from PyPI..."
    
    if ($UsePythonModule) {
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r $RequirementsFile
    } else {
        & $PipExecutable install --upgrade pip
        & $PipExecutable install -r $RequirementsFile
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies from PyPI."
        Exit 1
    }
}

Write-Host "Merging component database..."
if (Test-Path "merge_component_database.py") {
    & $VenvPython merge_component_database.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Component database merged successfully."
    } else {
        Write-Host "Warning: Component database merge had issues (this is not critical)."
    }
} else {
    Write-Host "merge_component_database.py not found, skipping database merge."
}

Write-Host ""
Write-Host "Installation script finished successfully."
Write-Host "You can launch the app from the Start Menu shortcut."

Stop-Transcript



Param()

Write-Host "Creating virtual environment..."
if (!(Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

Write-Host "Installing dependencies..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
  & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
} else {
  & .\.venv\Scripts\python.exe -m pip install pandas openpyxl python-docx pywin32
}

Write-Host "Done. You can launch the app from the Start Menu shortcut."



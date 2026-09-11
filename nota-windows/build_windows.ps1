$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

py -m pip install --upgrade pyinstaller
if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

py -m PyInstaller --noconfirm --clean --onefile --windowed --name Nota app.py
New-Item -ItemType Directory -Force release | Out-Null
Copy-Item dist\Nota.exe release\Nota-Windows.exe -Force
Write-Output "EXE creado en release\Nota-Windows.exe"
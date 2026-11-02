$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Run .\install.ps1 first to create the virtual environment."
}

& ".\.venv\Scripts\python.exe" -m pip install -r backend\requirements-speech.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install optional speech dependencies." }
Write-Host "Speech dependencies installed. Download a Vosk model or configure faster-whisper in .env."

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Run .\install.ps1 first."
}

& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000

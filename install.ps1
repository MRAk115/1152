$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ is required. Install Python and ensure it is on PATH."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js 20.19+ with npm is required. Install Node.js and ensure it is on PATH."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Review its settings before starting Jarvis."
}

python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Could not create the Python virtual environment." }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& ".\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install backend dependencies." }

Push-Location frontend
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "Could not install frontend dependencies." }
} finally {
    Pop-Location
}

Write-Host "Dependencies installed. Start the backend and frontend in separate terminals."

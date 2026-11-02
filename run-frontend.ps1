$ErrorActionPreference = "Stop"

if (-not (Test-Path "frontend\node_modules")) {
    throw "Run .\install.ps1 first."
}

Push-Location frontend
try {
    npm run dev
} finally {
    Pop-Location
}

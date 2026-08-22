param(
    [int]$Port = 8001
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
$database = Join-Path $root 'forest_wellness_local.db'

if (-not (Test-Path -LiteralPath $database)) {
    throw "Backend database is missing: $database"
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrapPython = Get-Command py -ErrorAction SilentlyContinue
    if (-not $bootstrapPython) {
        throw 'Python launcher (py) was not found. Install Python 3.11+ and run this script again.'
    }

    & $bootstrapPython.Source -3 -m venv (Join-Path $root '.venv')
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $root 'requirements.txt')
}

$env:DATABASE_URL_OVERRIDE = "sqlite:///$($database -replace '\\', '/')"
$env:SECRET_KEY = 'slky-local-development-secret-key-change-before-production'
$env:APP_DEBUG = 'true'

Push-Location $root
try {
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}

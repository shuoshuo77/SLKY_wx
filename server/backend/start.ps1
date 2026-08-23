param(
    [int]$Port = 8001
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $root '..\..')
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
$database = Join-Path $root 'forest_wellness_local.db'
$requirements = Join-Path $root 'requirements.txt'

function Import-EnvFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) {
            continue
        }

        $equalsIndex = $trimmed.IndexOf('=')
        if ($equalsIndex -lt 1) {
            continue
        }

        $key = $trimmed.Substring(0, $equalsIndex).Trim()
        $value = $trimmed.Substring($equalsIndex + 1).Trim().Trim('"').Trim("'")
        if (-not [Environment]::GetEnvironmentVariable($key, 'Process')) {
            [Environment]::SetEnvironmentVariable($key, $value, 'Process')
        }
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrapPython = Get-Command py -ErrorAction SilentlyContinue
    if (-not $bootstrapPython) {
        throw 'Python launcher (py) was not found. Install Python 3.11+ and run this script again.'
    }

    & $bootstrapPython.Source -3 -m venv (Join-Path $root '.venv')
    & $venvPython -m pip install --upgrade pip
}

& $venvPython -c "import alembic, uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $venvPython -m pip install -r $requirements
}

Import-EnvFile (Join-Path $projectRoot '.env')
Import-EnvFile (Join-Path $root '.env')

if (-not $env:DATABASE_URL_OVERRIDE -and -not $env:DB_HOST) {
    if (-not (Test-Path -LiteralPath $database)) {
        throw "Backend database is missing: $database"
    }
    $env:DATABASE_URL_OVERRIDE = "sqlite:///$($database -replace '\\', '/')"
}

$env:SECRET_KEY = 'slky-local-development-secret-key-change-before-production'
$env:APP_DEBUG = 'true'

Push-Location $root
try {
    & $venvPython -m alembic upgrade head
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}

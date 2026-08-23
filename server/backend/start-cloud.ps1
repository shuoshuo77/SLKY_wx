param(
    [int]$Port = 8001
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $root '..\..')
$configPath = Join-Path $projectRoot '.env.cloud'
$startScript = Join-Path $root 'start.ps1'

if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Missing cloud database config: $configPath"
}

$config = @{}
foreach ($line in Get-Content -LiteralPath $configPath -Encoding UTF8) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith('#')) {
        continue
    }

    $key, $value = $trimmed -split '=', 2
    if ($key -and $null -ne $value) {
        $config[$key.Trim()] = $value.Trim().Trim('"').Trim("'")
    }
}

$required = 'SSH_HOST','SSH_USER','SSH_PASSWORD','SSH_HOST_KEY','SSH_REMOTE_MYSQL_PORT','LOCAL_TUNNEL_PORT','DB_USER','DB_PASSWORD','DB_NAME'
foreach ($key in $required) {
    if (-not $config[$key]) {
        throw "Missing $key in .env.cloud"
    }
}

$localPort = [int]$config.LOCAL_TUNNEL_PORT
$existingTunnel = Get-NetTCPConnection -State Listen -LocalPort $localPort -ErrorAction SilentlyContinue
$tunnel = $null

if (-not $existingTunnel) {
    $plinkCommand = Get-Command plink.exe -ErrorAction SilentlyContinue
    $plinkPaths = @(@(
        $plinkCommand.Source,
        'C:\Program Files\PuTTY\plink.exe',
        'D:\New Folder\plink.exe'
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)

    if (-not $plinkPaths) {
        throw 'PuTTY plink.exe was not found. Install PuTTY or add plink.exe to PATH.'
    }

    $forward = "127.0.0.1:${localPort}:127.0.0.1:$($config.SSH_REMOTE_MYSQL_PORT)"
    $argumentLine = "-batch -N -ssh $($config.SSH_USER)@$($config.SSH_HOST) -P 22 -hostkey `"$($config.SSH_HOST_KEY)`" -pw `"$($config.SSH_PASSWORD)`" -L $forward"
    $tunnel = Start-Process -FilePath $plinkPaths[0] -ArgumentList $argumentLine -WindowStyle Hidden -PassThru

    Start-Sleep -Seconds 2
    if ($tunnel.HasExited) {
        throw 'SSH tunnel failed to start.'
    }
    if (-not (Get-NetTCPConnection -State Listen -LocalPort $localPort -ErrorAction SilentlyContinue)) {
        throw "SSH tunnel did not open local port $localPort."
    }
}

try {
    $dbPassword = [uri]::EscapeDataString($config.DB_PASSWORD)
    $env:DATABASE_URL_OVERRIDE = "mysql+pymysql://$($config.DB_USER):${dbPassword}@127.0.0.1:${localPort}/$($config.DB_NAME)?charset=utf8mb4"
    & $startScript -Port $Port
}
finally {
    Remove-Item Env:DATABASE_URL_OVERRIDE -ErrorAction SilentlyContinue
    if ($tunnel -and -not $tunnel.HasExited) {
        Stop-Process -Id $tunnel.Id
    }
}

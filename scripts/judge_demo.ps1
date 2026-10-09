[CmdletBinding()]
param([switch]$Stop)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$projectName = 'clearview_bi_judge'
$ports = @{
    CLEARVIEW_DB_HOST_PORT = '55432'
    CLEARVIEW_MOCK_HOST_PORT = '18001'
    CLEARVIEW_API_HOST_PORT = '18000'
    CLEARVIEW_WEB_HOST_PORT = '5175'
}
$previousPorts = @{}

Push-Location $repoRoot
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker is not installed. Install Docker Desktop, start it, then run this script again.'
    }

    if ($Stop) {
        docker compose --project-name $projectName down
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop the Clearview judge-demo stack.' }
        Write-Host 'Demo containers stopped. The demo database volume was kept.'
        return
    }

    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'Docker Desktop is not running. Open Docker Desktop, wait until it says Engine running, then retry.'
    }

    foreach ($name in $ports.Keys) {
        $previousPorts[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $ports[$name], 'Process')
    }

    docker compose --project-name $projectName up --build -d
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose could not start the demo stack.' }

    $healthUrl = "http://127.0.0.1:$($ports.CLEARVIEW_API_HOST_PORT)/api/v1/health"
    $deadline = (Get-Date).AddMinutes(2)
    $healthy = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 3
            if ($health.status -eq 'healthy') { $healthy = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $healthy) { throw "The API did not become healthy in time. Check: docker compose --project-name $projectName logs app postgres" }

    docker compose --project-name $projectName exec -T app python scripts/seed_demo_analytics.py
    if ($LASTEXITCODE -ne 0) { throw 'Could not load the synthetic judge dataset.' }

    Write-Host ''
    Write-Host 'Clearview BI demo is ready.' -ForegroundColor Green
    Write-Host "Open: http://127.0.0.1:$($ports.CLEARVIEW_WEB_HOST_PORT)"
    Write-Host 'Create a company account to claim the seeded demo workspace. No API keys are required.'
    Write-Host "To stop the demo and keep its data: .\scripts\judge_demo.ps1 -Stop"
} finally {
    foreach ($name in $ports.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousPorts[$name], 'Process')
    }
    Pop-Location
}

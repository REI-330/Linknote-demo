param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,
    [int]$FrontendPort = 0,
    [switch]$DryRun
)

# Stop stale LinkNote backend/frontend processes before starting a fresh local
# session. This avoids the common Windows issue where an old dev server keeps
# serving outdated code on the same port.

$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$backendRoot = [System.IO.Path]::Combine($resolvedRoot, "backend")
$frontendRoot = [System.IO.Path]::Combine($resolvedRoot, "frontend")

function Matches-LinkNoteProcess {
    param([string]$CommandLine)

    if ([string]::IsNullOrWhiteSpace($CommandLine)) {
        return $false
    }

    $isBackend = $CommandLine.Contains($backendRoot) -and (
        $CommandLine.Contains("python -m app.run_local") -or
        $CommandLine.Contains("python -m uvicorn") -or
        $CommandLine.Contains("multiprocessing-fork")
    )
    if ($isBackend) {
        return $true
    }

    $isFrontend = $CommandLine.Contains($frontendRoot) -and (
        $CommandLine.Contains("npm run dev") -or
        $CommandLine.Contains("vite")
    )
    return $isFrontend
}

function Get-ConfiguredBackendPort {
    $configPath = Join-Path $resolvedRoot "workspace\runtime\linknote.json"
    if (-not (Test-Path -LiteralPath $configPath)) {
        return 8765
    }

    try {
        $raw = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        $port = [int]$raw.server.port
        if ($port -gt 0) {
            return $port
        }
    } catch {
    }
    return 8765
}

function Get-ListeningPidsForPort {
    param([int]$Port)

    if ($Port -le 0) {
        return @()
    }

    $pattern = ":{0}\s" -f $Port
    return @(
        netstat -ano -p TCP |
            Select-String "LISTENING" |
            Where-Object { $_.Line -match $pattern } |
            ForEach-Object {
                if ($_.Line -match "LISTENING\s+(\d+)\s*$") {
                    $matches[1]
                }
            } |
            Where-Object { $_ -match "^\d+$" } |
            Sort-Object -Unique
    )
}

function Stop-Targets {
    param(
        [object[]]$Items,
        [string]$LabelProperty,
        [string]$IdProperty
    )

    if (-not $Items) {
        Write-Host "[LinkNote] No stale local processes found."
        exit 0
    }

    foreach ($item in $Items) {
        $summary = "{0} (PID {1})" -f $item.$LabelProperty, $item.$IdProperty
        if ($DryRun) {
            Write-Host "[LinkNote] Would stop $summary"
            continue
        }

        Write-Host "[LinkNote] Stopping $summary"
        & taskkill /F /T /PID $item.$IdProperty *> $null
    }
    exit 0
}

try {
    $processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
} catch {
    Write-Host "[LinkNote] Process inspection unavailable, falling back to port cleanup."
    $fallbackPort = Get-ConfiguredBackendPort
    $fallbackPids = @()
    $fallbackPids += Get-ListeningPidsForPort $fallbackPort
    $fallbackPids += Get-ListeningPidsForPort $FrontendPort
    $fallbackTargets = @(
        $fallbackPids |
            Sort-Object -Unique |
            ForEach-Object { [pscustomobject]@{ Name = "Port listener"; ProcessId = [int]$_ } }
    )
    Stop-Targets -Items $fallbackTargets -LabelProperty "Name" -IdProperty "ProcessId"
}

$targets = $processes |
    Where-Object { Matches-LinkNoteProcess $_.CommandLine } |
    Sort-Object ProcessId -Unique

Stop-Targets -Items $targets -LabelProperty "Name" -IdProperty "ProcessId"

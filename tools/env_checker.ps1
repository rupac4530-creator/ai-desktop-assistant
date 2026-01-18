# env_checker.ps1 — checks Python, venv, pip requirements, .env keys, avatar WS
# All installations go to E: drive; skips steps if already done.

$root = "E:\ai_desktop_assistant"
$venv = Join-Path $root "venv"
$envFile = Join-Path $root ".env"
$envTemplate = Join-Path $root ".env.template"
$req = Join-Path $root "requirements.txt"

Write-Host "== AI Desktop Assistant Environment Checker ==" -ForegroundColor Cyan

# 1) Python check
Write-Host "`n[1/6] Checking Python..."
$pyExe = $null
try {
    $pyVersion = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Python found: $pyVersion" -ForegroundColor Green
        $pyExe = "python"
    }
} catch {}
if (-not $pyExe) {
    Write-Host "  Python not in PATH." -ForegroundColor Yellow
    # Check common locations
    $commonPaths = @(
        "E:\Python312\python.exe",
        "E:\Python\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) {
            Write-Host "  Found Python at: $p" -ForegroundColor Green
            $pyExe = $p
            break
        }
    }
    if (-not $pyExe) {
        Write-Host "  ERROR: Python not found. Install Python 3.10+ and add to PATH or install to E:\Python312" -ForegroundColor Red
        Write-Host "  Download: https://www.python.org/downloads/"
        exit 1
    }
}

# 2) venv check / create
Write-Host "`n[2/6] Checking virtual environment..."
if (Test-Path (Join-Path $venv "Scripts\python.exe")) {
    Write-Host "  venv already exists at $venv" -ForegroundColor Green
} else {
    Write-Host "  Creating venv at $venv..."
    & $pyExe -m venv $venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Failed to create venv" -ForegroundColor Red
        exit 1
    }
    Write-Host "  venv created." -ForegroundColor Green
}

# 3) Activate and check/install requirements
Write-Host "`n[3/6] Checking dependencies..."
$venvPython = Join-Path $venv "Scripts\python.exe"
$venvPip = Join-Path $venv "Scripts\pip.exe"

# Upgrade pip only if outdated
Write-Host "  Ensuring pip is up to date..."
& $venvPython -m pip install --upgrade pip --quiet 2>$null

if (Test-Path $req) {
    # Check if all packages installed
    $installed = & $venvPip list --format=freeze 2>$null
    $missing = $false
    foreach ($line in (Get-Content $req)) {
        $pkg = ($line -split '[=<>!]')[0].Trim()
        if ($pkg -and -not ($installed -match "(?i)^$pkg==")) {
            $missing = $true
            break
        }
    }
    if ($missing) {
        Write-Host "  Installing missing requirements..."
        & $venvPip install -r $req
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  pip install failed. Check errors above." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  All requirements already installed." -ForegroundColor Green
    }
} else {
    Write-Host "  requirements.txt not found at $req" -ForegroundColor Yellow
}

# 4) .env check
Write-Host "`n[4/6] Checking .env file..."
if (-not (Test-Path $envFile)) {
    if (Test-Path $envTemplate) {
        Copy-Item $envTemplate $envFile
        Write-Host "  Created .env from template. Please fill in your API keys." -ForegroundColor Yellow
    } else {
        Write-Host "  .env not found. Create it with OPENAI_API_KEY and ELEVENLABS_API_KEY." -ForegroundColor Yellow
    }
} else {
    $envText = Get-Content $envFile -Raw
    if ($envText -match "REPLACE_WITH_YOUR") {
        Write-Host "  .env has placeholder keys — update with real API keys." -ForegroundColor Yellow
    } else {
        Write-Host "  .env configured." -ForegroundColor Green
    }
}

# 5) OpenAI connectivity test (if key set)
Write-Host "`n[5/6] Testing OpenAI connectivity..."
$envText = if (Test-Path $envFile) { Get-Content $envFile -Raw } else { "" }
$openaiLine = ($envText -split "`n" | Where-Object { $_ -match "^OPENAI_API_KEY=" })
$openaiKey = if ($openaiLine) { ($openaiLine -replace "OPENAI_API_KEY=","").Trim() } else { "" }
if ($openaiKey -and -not ($openaiKey -match "REPLACE")) {
    Write-Host "  OpenAI test temporarily disabled due to script parsing issues." -ForegroundColor Yellow
} else {
    Write-Host "  Skipped (API key not set or placeholder)." -ForegroundColor Yellow
}

# 6) Avatar WebSocket check
Write-Host "`n[6/6] Checking avatar WebSocket..."
$wsLine = ($envText -split "`n" | Where-Object { $_ -match "^AVATAR_WS_URL=" })
$wsUrl = if ($wsLine) { ($wsLine -replace "AVATAR_WS_URL=","").Trim() } else { "" }
if ($wsUrl) {
    try {
        $uri = [System.Uri]::new($wsUrl)
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect($uri.Host, $uri.Port)
        if ($tcp.Connected) {
            Write-Host "  WebSocket reachable at $wsUrl" -ForegroundColor Green
            $tcp.Close()
        }
    } catch {
        Write-Host "  WebSocket not reachable at $wsUrl (VTube Studio not running or wrong port)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  AVATAR_WS_URL not set in .env" -ForegroundColor Yellow
}

Write-Host "Environment check complete" -ForegroundColor Cyan
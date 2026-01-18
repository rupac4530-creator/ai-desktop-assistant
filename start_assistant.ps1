# Start AI Desktop Assistant
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

# Activate venv
& "$ROOT\venv\Scripts\Activate.ps1"

# Set PYTHONPATH
$env:PYTHONPATH = $ROOT

# Start Ollama if not running
$ollamaRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Write-Host "Starting Ollama..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# Start AutoHotkey overlay
$ahkPath = "$ROOT\tools\vt_overlay.ahk"
if (Test-Path $ahkPath) {
    Start-Process -FilePath "C:\Program Files\AutoHotkey\AutoHotkey.exe" -ArgumentList $ahkPath -WindowStyle Hidden
}

# Run assistant
python "$ROOT\core\main_controller.py"

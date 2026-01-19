@echo off
REM ============================================================
REM Create a distribution ZIP of the AI Desktop Assistant
REM ============================================================
REM This creates a clean ZIP without:
REM   - .env (secrets)
REM   - venv/ (virtual environment)
REM   - logs/ (runtime logs)
REM   - __pycache__/ (Python cache)
REM   - .git/ (repository data)
REM ============================================================

echo.
echo ========================================
echo   AI Desktop Assistant - Create ZIP
echo ========================================
echo.

set VERSION=1.0.0
set ZIPNAME=ai-desktop-assistant-v%VERSION%.zip

REM Check if 7-Zip is available
where 7z >nul 2>&1
if errorlevel 1 (
    echo [!] 7-Zip not found. Using PowerShell...
    goto :powershell_zip
)

:sevenzip
echo [*] Creating %ZIPNAME% with 7-Zip...
7z a -tzip %ZIPNAME% ^
    -xr!.git ^
    -xr!.env ^
    -xr!venv ^
    -xr!logs ^
    -xr!__pycache__ ^
    -xr!*.pyc ^
    -xr!.mypy_cache ^
    -xr!.pytest_cache ^
    -xr!dist ^
    -xr!build ^
    -xr!*.egg-info ^
    *
goto :done

:powershell_zip
echo [*] Creating %ZIPNAME% with PowerShell...
powershell -Command ^
    "$exclude = @('.git', '.env', 'venv', 'logs', '__pycache__', '.mypy_cache', '.pytest_cache', 'dist', 'build'); ^
    $files = Get-ChildItem -Recurse | Where-Object { $relativePath = $_.FullName.Replace((Get-Location).Path + '\', ''); $shouldExclude = $false; foreach ($ex in $exclude) { if ($relativePath -like \"$ex*\" -or $relativePath -like \"*\$ex*\") { $shouldExclude = $true; break } }; -not $shouldExclude }; ^
    Compress-Archive -Path (Get-ChildItem -Exclude .git,.env,venv,logs,__pycache__,.mypy_cache,.pytest_cache,dist,build) -DestinationPath '%ZIPNAME%' -Force"
goto :done

:done
echo.
echo ========================================
echo   ZIP CREATED: %ZIPNAME%
echo ========================================
echo.
echo   Contents excluded:
echo   - .env (secrets)
echo   - venv/ (virtual environment)
echo   - logs/ (runtime logs)
echo   - .git/ (repository)
echo   - __pycache__/ (Python cache)
echo.
echo   Ready to share!
echo.
pause

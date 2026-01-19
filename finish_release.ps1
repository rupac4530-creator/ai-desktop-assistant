# -------------------- CONFIG (DO NOT CHANGE unless you MUST) --------------------
$PROJECT_ROOT = "E:\ai_desktop_assistant"
$DEMO_SRC_PATH = "E:\temp\2C72E5A7710B4CAC8A67AA29FBC98E3C\OneDriveDeltaPatch\Bundle\Assets\freView\assets\demo_screenshot.png"
$DEMO_DEST_PATH = Join-Path $PROJECT_ROOT "assets\demo_screenshot.png"
$GITHUB_REPO_URL = "https://github.com/Bedanta/ai-desktop-assistant.git"
$GIT_AUTHOR_NAME = "Bedanta Chatterjee"
$GIT_AUTHOR_EMAIL = "rupac4530@gmail.com"
$RELEASE_TAG = "v1.0.1"
$RELEASE_MESSAGE = "Release v1.0.1 - include demo screenshot and author name"
$LOG_DIR = Join-Path $PROJECT_ROOT "logs"
$ERROR_LOG = Join-Path $LOG_DIR "finish_release_errors.txt"
$REPORT = Join-Path $LOG_DIR "release_completion_report.txt"
# -----------------------------------------------------------------------------

# helper: log + exit on error
function Fail([string]$msg){
    if (-not (Test-Path $LOG_DIR)) { New-Item -Path $LOG_DIR -ItemType Directory -Force | Out-Null }
    $ts = (Get-Date).ToString("s")
    "$ts  ERROR: $msg" | Out-File -FilePath $ERROR_LOG -Append -Encoding utf8
    Write-Host "ERROR: $msg"
    exit 1
}

# 0) Environment checks
if (-not (Test-Path $PROJECT_ROOT)) { Fail "PROJECT_ROOT not found: $PROJECT_ROOT" }
if (-not (Test-Path $DEMO_SRC_PATH))  { Fail "DEMO_SRC_PATH not found: $DEMO_SRC_PATH" }

# Find git
$gitExe = $null
$possibleGitPaths = @(
    "E:\Git\bin\git.exe",
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "C:\Git\bin\git.exe",
    "git.exe"  # if in PATH
)
foreach ($path in $possibleGitPaths) {
    if (Test-Path $path) {
        $gitExe = $path
        break
    }
}
if (-not $gitExe) { Fail "git not found in PATH or common locations." }

# create logs dir
if (-not (Test-Path $LOG_DIR)) { New-Item -Path $LOG_DIR -ItemType Directory -Force | Out-Null }

"START: $(Get-Date -Format 's')" | Out-File -FilePath $REPORT -Encoding utf8

# 1) Copy demo screenshot to repo
Write-Host "1) Copy demo screenshot to repo"
Copy-Item -Path $DEMO_SRC_PATH -Destination $DEMO_DEST_PATH -Force -ErrorAction Stop
"Copied demo screenshot: $DEMO_SRC_PATH -> $DEMO_DEST_PATH" | Out-File -FilePath $REPORT -Append -Encoding utf8

# 2) Replace author name in LICENSE
$licensePath = Join-Path $PROJECT_ROOT "LICENSE"
if (Test-Path $licensePath) {
    Write-Host "2) Updating LICENSE author"
    (Get-Content $licensePath -Raw) -replace "\[Your Name\]","Bedanta Chatterjee" | Set-Content $licensePath -Encoding utf8
    "Updated LICENSE author placeholder." | Out-File -FilePath $REPORT -Append -Encoding utf8
} else {
    "LICENSE not found; skipping update." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 3) Update README.md placeholders and ensure author/GitHub/release lines
$readmePath = Join-Path $PROJECT_ROOT "README.md"
if (Test-Path $readmePath) {
    Write-Host "3) Updating README.md placeholders"
    $readmeContents = Get-Content $readmePath
    $readmeContents = $readmeContents -replace "YOURNAME|Your Name|REPLACE_WITH_NAME","Bedanta Chatterjee"
    # Ensure author line present
    if ($readmeContents -notmatch "Author:\s*Bedanta Chatterjee") {
        $readmeContents = @("Author: Bedanta Chatterjee","GitHub: $GITHUB_REPO_URL","Release: $RELEASE_TAG","") + $readmeContents
    }
    $readmeContents | Set-Content $readmePath -Encoding utf8
    "README.md updated." | Out-File -FilePath $REPORT -Append -Encoding utf8
} else {
    "README.md not found; skipping update." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 4) Set local git user
Write-Host "4) Setting local git user config"
Push-Location $PROJECT_ROOT
& $gitExe config user.name "$GIT_AUTHOR_NAME"
& $gitExe config user.email "$GIT_AUTHOR_EMAIL"
'git user set: $GIT_AUTHOR_NAME <$GIT_AUTHOR_EMAIL>' | Out-File -FilePath $REPORT -Append -Encoding utf8

# 5) Stage files
Write-Host "5) Staging files"
& $gitExe add "assets/demo_screenshot.png" LICENSE README.md 2>$null
"git status (after add):" | Out-File -FilePath $REPORT -Append -Encoding utf8
& $gitExe status --porcelain | Out-File -FilePath $REPORT -Append -Encoding utf8

# 6) Commit
Write-Host "6) Committing changes"
$commitMessage = "chore(release): add demo screenshot and set author to Bedanta Chatterjee"
# try commit, if no changes this will fail harmlessly
$commitResult = & $gitExe commit -m $commitMessage 2>&1
$commitResult | Out-File -FilePath $REPORT -Append -Encoding utf8

# 7) Ensure origin remote exists
$originUrl = & $gitExe remote get-url origin 2>$null
if (-not $originUrl) {
    Write-Host "7) Adding remote origin $GITHUB_REPO_URL"
    & $gitExe remote add origin $GITHUB_REPO_URL 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8
} else {
    "Origin remote already set: $originUrl" | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 8) Push branch to remote main
Write-Host "8) Pushing branch to origin:main"
$pushOut = & $gitExe push origin HEAD:main 2>&1
$pushOut | Out-File -FilePath $REPORT -Append -Encoding utf8
if ($pushOut -match "ERROR") { Fail "git push failed. See report." }

# 9) Create annotated tag and push
Write-Host "9) Creating tag $RELEASE_TAG"
# delete local tag if exists then create fresh
if (& $gitExe tag --list | Select-String -Pattern ("^$RELEASE_TAG$")) {
    & $gitExe tag -d $RELEASE_TAG 2>$null
}
& $gitExe tag -a $RELEASE_TAG -m "$RELEASE_MESSAGE"
& $gitExe push origin $RELEASE_TAG 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8

# 10) Build zip if script exists
$zipScript = Join-Path $PROJECT_ROOT "create_release_zip.bat"
$zipPath = Join-Path $PROJECT_ROOT "ai-desktop-assistant-v1.0.0.zip"
if (Test-Path $zipScript) {
    Write-Host "10) Running create_release_zip.bat"
    & $zipScript 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8
    Start-Sleep -Seconds 2
    if (Test-Path $zipPath) {
        "ZIP built: $zipPath" | Out-File -FilePath $REPORT -Append -Encoding utf8
    } else {
        "ZIP build script ran but zip not found at $zipPath" | Out-File -FilePath $REPORT -Append -Encoding utf8
    }
} else {
    "No create_release_zip.bat - skipping ZIP build." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 11) If gh available, create GitHub release and attach zip if any
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "11) GH CLI detected - creating release"
    if (Test-Path $zipPath) {
        gh release create $RELEASE_TAG $zipPath -t $RELEASE_TAG -n "$RELEASE_MESSAGE" 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8
    } else {
        gh release create $RELEASE_TAG -t $RELEASE_TAG -n "$RELEASE_MESSAGE" 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8
    }
    "GH release create step done." | Out-File -FilePath $REPORT -Append -Encoding utf8
} else {
    "gh CLI not present - release must be created manually on GitHub." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 12) Run smoke test (tools/test_multitask.py) and save output
$smokeScript = Join-Path $PROJECT_ROOT "tools\test_multitask.py"
if (Test-Path $smokeScript) {
    Write-Host "12) Running smoke test script"
    $pythonExe = Join-Path $PROJECT_ROOT ".\venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) { Fail "Python venv interpreter not found at $pythonExe" }
    & $pythonExe $smokeScript > (Join-Path $LOG_DIR "smoke_run_report.txt") 2>&1
    "Smoke test output saved to logs\smoke_run_report.txt" | Out-File -FilePath $REPORT -Append -Encoding utf8
} else {
    "Smoke test script not found; skipping." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 13) Take screenshot of GitHub release page (use Playwright if available)
$releaseUrl = "https://github.com/Bedanta/ai-desktop-assistant/releases/tag/$RELEASE_TAG"
$releaseScreenshot = Join-Path $PROJECT_ROOT "assets\release_screenshot.png"
Write-Host "13) Capturing release page screenshot: $releaseUrl"
# Try Playwright python script, fall back to opening page and requesting user screenshot
$playwrightScript = @'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1400,'height':900})
    page.goto('$releaseUrl', timeout=60000)
    page.wait_for_timeout(2000)
    page.screenshot(path=r'${releaseScreenshot}', full_page=True)
    browser.close()
'@
$playwrightFile = Join-Path $PROJECT_ROOT "tools\take_release_screenshot.py"
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$playwrightInstalled = $false
if ($pythonCmd) {
    & python -c "import playwright" 2>$null
    $playwrightInstalled = $LASTEXITCODE -eq 0
}
# Save script
$playwrightScript | Out-File -FilePath $playwrightFile -Encoding utf8
if ($playwrightInstalled) {
    Write-Host "Running Playwright screenshot script..."
    python $playwrightFile 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8
    if (Test-Path $releaseScreenshot) {
        "Release page screenshot saved to assets\release_screenshot.png" | Out-File -FilePath $REPORT -Append -Encoding utf8
    } else {
        "Playwright ran but screenshot missing." | Out-File -FilePath $REPORT -Append -Encoding utf8
    }
} else {
    "Playwright or python playwright not available - saved script to tools/take_release_screenshot.py. Please run it when Playwright is installed." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 14) Generate docs/onepager (HTML and try headless Edge -> PDF)
$onepageHtml = Join-Path $PROJECT_ROOT "docs\onepager.html"
$onepagePdf  = Join-Path $PROJECT_ROOT "docs\onepager.pdf"
if (-not (Test-Path (Join-Path $PROJECT_ROOT "docs"))) { New-Item -Path (Join-Path $PROJECT_ROOT "docs") -ItemType Directory | Out-Null }
$onepageContent = @"
<!doctype html>
<html>
<head><meta charset='utf-8'><title>AI Desktop Assistant â€” One Pager</title></head>
<body>
<h1>AI Desktop Assistant â€” v1.0.1</h1>
<p><strong>Author:</strong> Bedanta Chatterjee</p>
<p><strong>GitHub:</strong> $GITHUB_REPO_URL</p>
<h2>Short description</h2>
<p>Self-healing, offline-first desktop assistant with STT, TTS, OCR, automation, and autonomous patching.</p>
<h2>Features</h2>
<ul>
<li>Push-to-talk and typed commands</li>
<li>Self-healing watchdog & automated repair</li>
<li>Git-backed autonomous fixes</li>
<li>Playwright browser automation and OCR</li>
</ul>
<p><img src='../assets/demo_screenshot.png' style='max-width:800px;'></p>
<p>Contact: $GIT_AUTHOR_NAME â€” $GIT_AUTHOR_EMAIL</p>
</body>
</html>
"@
$onepageContent | Out-File -FilePath $onepageHtml -Encoding utf8
"onepager HTML written to docs\onepager.html" | Out-File -FilePath $REPORT -Append -Encoding utf8

# Attempt headless Edge print to PDF
$msedge = (Get-Command msedge.exe -ErrorAction SilentlyContinue).Source
if ($msedge) {
    Write-Host "14) Using msedge headless to print PDF"
    & $msedge --headless --disable-gpu --print-to-pdf="$onepagePdf" "file:///$onepageHtml" 2>&1 | Out-File -FilePath $REPORT -Append -Encoding utf8
    if (Test-Path $onepagePdf) {
        "onepager PDF generated at docs/onepager.pdf" | Out-File -FilePath $REPORT -Append -Encoding utf8
    } else {
        "msedge print-to-pdf failed or not supported; HTML saved at docs/onepager.html" | Out-File -FilePath $REPORT -Append -Encoding utf8
    }
} else {
    "msedge not found; onepager HTML saved; convert to PDF manually." | Out-File -FilePath $REPORT -Append -Encoding utf8
}

# 15) Prepare LinkedIn post & Email template (write files)
$liPath = Join-Path $PROJECT_ROOT "assets\linkedin_post.txt"
$emailPath = Join-Path $PROJECT_ROOT "assets\recruiter_email.txt"
$liText = @"
I just released v1.0 of my open-source project: AI Desktop Assistant â€” a self-healing, offline-first desktop assistant with voice, TTS, OCR, and autonomous repair. ðŸš€

Demo + code: $GITHUB_REPO_URL
Release: $GITHUB_REPO_URL/releases/tag/$RELEASE_TAG

Iâ€™m Bedanta Chatterjee â€” looking for remote/onsite roles in AI tooling, developer tools, and automation. Open to referrals and internships. #opensource #python #ai
"@
$emailText = @"
Subject: AI Desktop Assistant (open-source) â€” Bedanta Chatterjee â€” available for roles

Hi [Name],

My name is Bedanta Chatterjee. I recently built and open-sourced an AI Desktop Assistant (Python). Itâ€™s an autonomous, self-healing assistant with offline-first LLM integration, voice commands (PTT), TTS, OCR and Git-backed autonomous repair. Itâ€™s packaged with docs and a release:

GitHub: $GITHUB_REPO_URL
Release: $GITHUB_REPO_URL/releases/tag/$RELEASE_TAG

Iâ€™m actively looking for roles in AI tooling, automation, or developer experience. Iâ€™d appreciate a chance to interview or demonstrate the project.

Thanks,
Bedanta Chatterjee
Email: $GIT_AUTHOR_EMAIL
"@
$liText | Out-File -FilePath $liPath -Encoding utf8
$emailText | Out-File -FilePath $emailPath -Encoding utf8
"LinkedIn post and email templates stored in assets\." | Out-File -FilePath $REPORT -Append -Encoding utf8

# 16) Final report: list of created/updated files and success
$results = @()
if (Test-Path $DEMO_DEST_PATH) { $results += "demo screenshot: OK" } else { $results += "demo screenshot: MISSING" }
if (Test-Path $licensePath) { $results += "LICENSE updated" } else { $results += "LICENSE missing or unchanged" }
if (Test-Path $readmePath) { $results += "README updated" } else { $results += "README missing or unchanged" }
if (Test-Path $zipPath) { $results += "ZIP: $zipPath" } else { $results += "ZIP: not present" }
if (Test-Path (Join-Path $LOG_DIR "smoke_run_report.txt")) { $results += "smoke test: logs/smoke_run_report.txt" } else { $results += "smoke test: not run" }
if (Test-Path $releaseScreenshot) { $results += "release screenshot: assets/release_screenshot.png" } else { $results += "release screenshot: not created" }
if (Test-Path $onepagePdf) { $results += "onepager PDF: docs/onepager.pdf" } else { $results += "onepager PDF: not created (HTML saved)" }

"COMPLETION SUMMARY - $(Get-Date -Format 's')" | Out-File -FilePath $REPORT -Append -Encoding utf8
$results | Out-File -FilePath $REPORT -Append -Encoding utf8

Write-Host "FINISHED: see report at $REPORT"
Pop-Location


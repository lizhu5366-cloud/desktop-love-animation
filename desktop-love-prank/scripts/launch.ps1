# launch.ps1 — desktop-love-prank launcher
# Auto-detects Python, ensures Pillow, then runs run.py with forwarded args.

$ErrorActionPreference = "Stop"
$SkillDir = Split-Path -Parent $PSScriptRoot
$RunPy = Join-Path $PSScriptRoot "run.py"

# --- 1. Find a usable Python (must have tkinter) ---
$candidates = @()
try { $py = (Get-Command py -ErrorAction Stop).Source; $candidates += @{ exe = $py; args = "-3" } } catch {}
try { $py = (Get-Command python -ErrorAction Stop).Source; $candidates += @{ exe = $py; args = "" } } catch {}
try { $py = (Get-Command python3 -ErrorAction Stop).Source; $candidates += @{ exe = $py; args = "" } } catch {}

$python = $null
$pyArgs = ""
foreach ($c in $candidates) {
    $test = & $c.exe $c.args -c "import tkinter; print('ok')" 2>&1
    if ($LASTEXITCODE -eq 0 -and $test -match "ok") {
        $python = $c.exe
        $pyArgs = $c.args
        break
    }
}

if (-not $python) {
    Write-Host "[love-prank] Error: No Python with tkinter found. Install Python from python.org and check 'Add to PATH'." -ForegroundColor Red
    exit 1
}

# --- 2. Ensure Pillow ---
$pillow = & $python $pyArgs -c "import PIL; print('ok')" 2>&1
if ($LASTEXITCODE -ne 0 -or $pillow -notmatch "ok") {
    Write-Host "[love-prank] Installing Pillow..." -ForegroundColor Yellow
    & $python $pyArgs -m pip install --quiet Pillow
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[love-prank] Error: Failed to install Pillow. Run manually: pip install Pillow" -ForegroundColor Red
        exit 1
    }
}

# --- 3. Launch run.py in background, forward all args ---
$allArgs = @()
if ($pyArgs) { $allArgs += $pyArgs }
$allArgs += "`"$RunPy`""
# Forward caller args (everything after the script name)
$allArgs += $args

Start-Process -FilePath $python -ArgumentList $allArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
Write-Host "[love-prank] Started. Press Esc on screen to close." -ForegroundColor Green

param(
  [string]$Python = "py"
)

function Resolve-Python {
  param([string]$Candidate)
  if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
    try { & $Candidate -V | Out-Null; return $Candidate } catch {}
  }
  if (Get-Command "python" -ErrorAction SilentlyContinue) { return "python" }
  if (Get-Command "py" -ErrorAction SilentlyContinue) { return "py" }
  throw "Python launcher not found. Install Python 3.11+ or fix PATH."
}

function Resolve-Makensis {
  $cmd = Get-Command "makensis" -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Path }
  $candidates = @(
    "C:\\Program Files (x86)\\NSIS\\makensis.exe",
    "C:\\Program Files\\NSIS\\makensis.exe"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
  return $null
}

$makensis = Resolve-Makensis
if (-not $makensis) {
  throw "NSIS (makensis) not found. Install NSIS and ensure makensis is in PATH."
}

$root = Split-Path $PSScriptRoot -Parent
$assetPath = Join-Path $root 'assets'
$iconPath = Join-Path $assetPath 'clock.ico'

$py = Resolve-Python $Python
& $py -m pip install -r requirements.txt

& $py -m PyInstaller --clean --noconfirm --onedir --name WorldTimeSpecialist app.py `
  --icon "$iconPath" --add-data "$assetPath;assets" --collect-data tzdata --specpath build\onedir

if (-not (Test-Path release)) { New-Item -ItemType Directory -Force release | Out-Null }

& $makensis installer\WorldTimeSpecialist.nsi

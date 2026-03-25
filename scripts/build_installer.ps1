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

if (-not (Get-Command "makensis" -ErrorAction SilentlyContinue)) {
  throw "NSIS (makensis) not found. Install NSIS and ensure makensis is in PATH."
}

$py = Resolve-Python $Python
& $py -m pip install -r requirements.txt

& $py -m PyInstaller --clean --noconfirm --onedir --name WorldTimeSpecialist app.py `
  --icon assets\clock.ico --add-data "assets;assets" --collect-data tzdata

if (-not (Test-Path release)) { New-Item -ItemType Directory -Force release | Out-Null }

& makensis installer\WorldTimeSpecialist.nsi

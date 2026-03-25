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

$root = Split-Path $PSScriptRoot -Parent
$assetPath = Join-Path $root 'assets'
$iconPath = Join-Path $assetPath 'clock.ico'

$py = Resolve-Python $Python
& $py -m pip install -r requirements.txt

if (-not (Test-Path release)) { New-Item -ItemType Directory -Force release | Out-Null }

if (Test-Path dist) { Remove-Item -Recurse -Force dist }

# Portable EXE (onefile via spec)
& $py -m PyInstaller --clean WorldTimeSpecialist.spec
Copy-Item -Force dist\WorldTimeSpecialist.exe release\WorldTimeSpecialist-Portable.exe

# One-dir build for installer (spec to separate folder to avoid overwriting)
& $py -m PyInstaller --clean --noconfirm --onedir --name WorldTimeSpecialist app.py `
  --icon "$iconPath" --add-data "$assetPath;assets" --collect-data tzdata --specpath build\onedir

$makensis = Resolve-Makensis
if ($makensis) {
  & $makensis installer\WorldTimeSpecialist.nsi
} else {
  Write-Warning "NSIS (makensis) not found. Installer EXE not created."
}

# Checksums
if (Test-Path release\checksums.txt) { Remove-Item -Force release\checksums.txt }
"WorldTimeSpecialist-Portable.exe" | ForEach-Object {
  if (Test-Path "release\$_") {
    $h = Get-FileHash "release\$_" -Algorithm SHA256
    "{0}  {1}" -f $h.Hash, $_ | Out-File -FilePath release\checksums.txt -Encoding ASCII -Append
  }
}
if (Test-Path "release\WorldTimeSpecialist-Setup.exe") {
  $h = Get-FileHash "release\WorldTimeSpecialist-Setup.exe" -Algorithm SHA256
  "{0}  {1}" -f $h.Hash, "WorldTimeSpecialist-Setup.exe" | Out-File -FilePath release\checksums.txt -Encoding ASCII -Append
}

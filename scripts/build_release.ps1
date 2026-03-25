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

$py = Resolve-Python $Python

if (-not (Test-Path release)) { New-Item -ItemType Directory -Force release | Out-Null }

# Portable EXE
& $py -m PyInstaller --clean WorldTimeSpecialist.spec
Copy-Item -Force dist\WorldTimeSpecialist.exe release\WorldTimeSpecialist-Portable.exe

# One-dir build for installer
& $py -m PyInstaller --clean --noconfirm --onedir --name WorldTimeSpecialist app.py `
  --icon assets\clock.ico --add-data "assets;assets" --collect-data tzdata

if (Get-Command "makensis" -ErrorAction SilentlyContinue) {
  & makensis installer\WorldTimeSpecialist.nsi
} else {
  Write-Warning "NSIS (makensis) not found. Installer EXE not created."
}

# Checksums
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

param(
  [string]$Python = "py"
)

function Resolve-Python {
  param([string]$Candidate)
  if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
    try {
      & $Candidate -V | Out-Null
      return $Candidate
    } catch {}
  }
  if (Get-Command "python" -ErrorAction SilentlyContinue) { return "python" }
  if (Get-Command "py" -ErrorAction SilentlyContinue) { return "py" }
  throw "Python launcher not found. Install Python 3.11+ or fix PATH."
}

$py = Resolve-Python $Python
& $py -m PyInstaller --clean WorldTimeSpecialist.spec

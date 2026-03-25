param(
  [string]$Version = "v1.0.0"
)

if (-not (Get-Command "gh" -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI (gh) not found. Install gh and authenticate first."
}

$assets = @()
if (Test-Path "release\WorldTimeSpecialist-Portable.exe") { $assets += "release\WorldTimeSpecialist-Portable.exe" }
if (Test-Path "release\WorldTimeSpecialist-Setup.exe") { $assets += "release\WorldTimeSpecialist-Setup.exe" }
if (Test-Path "release\checksums.txt") { $assets += "release\checksums.txt" }

if ($assets.Count -eq 0) {
  throw "No release assets found in .\release. Run scripts\build_release.ps1 first."
}

gh release create $Version $assets -F release_notes.md -t "World Time Specialist 1.0.0"

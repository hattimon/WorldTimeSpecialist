param(
  [string]$Version = "v1.0.2"
)

$gh = if (Test-Path ".\tools\gh\bin\gh.exe") { ".\tools\gh\bin\gh.exe" } else { "gh" }

$assets = @()
if (Test-Path "release\WorldTimeSpecialist-Portable.exe") { $assets += "release\WorldTimeSpecialist-Portable.exe" }
if (Test-Path "release\WorldTimeSpecialist-Setup.exe") { $assets += "release\WorldTimeSpecialist-Setup.exe" }
if (Test-Path "release\checksums.txt") { $assets += "release\checksums.txt" }
if (Test-Path "release\build-scripts.zip") { $assets += "release\build-scripts.zip" }

if ($assets.Count -eq 0) {
  throw "No release assets found in .\release. Run scripts\build_release.ps1 first."
}

& $gh release create $Version $assets -F release_notes.md -t "World Time Specialist 1.0.2" -R hattimon/WorldTimeSpecialist


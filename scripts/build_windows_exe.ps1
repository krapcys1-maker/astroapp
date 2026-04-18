param()

$ErrorActionPreference = "Stop"

function Get-ProjectVersion {
    $versionLine = Get-Content "$PSScriptRoot\..\pyproject.toml" |
        Where-Object { $_ -match '^version = "' } |
        Select-Object -First 1
    if (-not $versionLine) {
        throw "Could not find project version in pyproject.toml."
    }
    return ($versionLine -replace '^version = "([^"]+)"$', '$1')
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$version = Get-ProjectVersion
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$buildRoot = Join-Path $repoRoot "build\windows-exe"
$pyinstallerWork = Join-Path $buildRoot "pyinstaller"
$distRoot = Join-Path $repoRoot "dist"
$portableExe = Join-Path $distRoot ("AstroLabb-{0}.exe" -f $version)
$pyinstallerExe = Join-Path $distRoot "AstroLabb.exe"

Remove-Item -LiteralPath $pyinstallerWork -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $portableExe -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $pyinstallerExe -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $pyinstallerWork | Out-Null
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

Push-Location $repoRoot
try {
    & $pythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name AstroLabb `
        --icon "app\resources\branding\astrolabb-icon.ico" `
        --add-data "app\resources;resources" `
        --hidden-import PySide6.QtSvg `
        --hidden-import swisseph `
        --hidden-import geopy.geocoders `
        --hidden-import geopy.exc `
        --hidden-import tzfpy `
        --distpath $distRoot `
        --workpath $pyinstallerWork `
        app\main.py
}
finally {
    Pop-Location
}

if (-not (Test-Path $pyinstallerExe)) {
    throw "Portable executable was not created: $pyinstallerExe"
}

Move-Item -LiteralPath $pyinstallerExe -Destination $portableExe -Force
Write-Host "Created portable executable: $portableExe"

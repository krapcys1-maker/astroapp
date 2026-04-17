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

$buildRoot = Join-Path $repoRoot "build\windows-installer"
$pyinstallerWork = Join-Path $buildRoot "pyinstaller"
$packageRoot = Join-Path $buildRoot "package"
$payloadRoot = Join-Path $buildRoot "payload"
$distRoot = Join-Path $repoRoot "dist"
$payloadTar = Join-Path $packageRoot "AstroLabb-payload.tar"
$setupExe = Join-Path $distRoot ("AstroLabb-Setup-{0}.exe" -f $version)
$sedPath = Join-Path $buildRoot "AstroLabb-Setup.sed"

Remove-Item -LiteralPath $pyinstallerWork -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $packageRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $payloadRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $payloadTar -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $setupExe -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $pyinstallerWork | Out-Null
New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null
New-Item -ItemType Directory -Force -Path $payloadRoot | Out-Null
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

Push-Location $repoRoot
try {
    & $pythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name AstroLabb `
        --add-data "app\resources;resources" `
        --hidden-import PySide6.QtSvg `
        --hidden-import swisseph `
        --hidden-import geopy.geocoders `
        --hidden-import geopy.exc `
        --hidden-import tzfpy `
        --distpath $payloadRoot `
        --workpath $pyinstallerWork `
        app\main.py
}
finally {
    Pop-Location
}

$appDir = Join-Path $payloadRoot "AstroLabb"
if (-not (Test-Path $appDir)) {
    throw "PyInstaller build output not found: $appDir"
}

& tar -cf $payloadTar -C $appDir .
if (-not (Test-Path $payloadTar)) {
    throw "Installer payload archive was not created: $payloadTar"
}

Copy-Item (Join-Path $repoRoot "scripts\installer\install.cmd") (Join-Path $packageRoot "install.cmd") -Force
Copy-Item (Join-Path $repoRoot "scripts\installer\install.ps1") (Join-Path $packageRoot "install.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\installer\uninstall.cmd") (Join-Path $packageRoot "uninstall.cmd") -Force

$sedContent = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=
DisplayLicense=
FinishMessage=AstroLabb has been installed for the current user.
TargetName=$setupExe
FriendlyName=AstroLabb Setup
AppLaunched=cmd.exe /d /s /c install.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=cmd.exe /d /s /c install.cmd /quiet
FILE0=AstroLabb-payload.tar
FILE1=install.cmd
FILE2=install.ps1
FILE3=uninstall.cmd
[SourceFiles]
SourceFiles0=$packageRoot\
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
%FILE3%=
"@

Set-Content -Path $sedPath -Value $sedContent -Encoding ASCII
& "$env:SystemRoot\System32\iexpress.exe" /N $sedPath

for ($attempt = 0; $attempt -lt 120 -and -not (Test-Path $setupExe); $attempt++) {
    Start-Sleep -Milliseconds 500
}

if (-not (Test-Path $setupExe)) {
    throw "Installer build failed: $setupExe was not created."
}

Write-Host "Created installer: $setupExe"

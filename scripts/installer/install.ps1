param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$packageRoot = $PSScriptRoot
$payloadTar = Join-Path $packageRoot "AstroLabb-payload.tar"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\AstroLabb"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\AstroLabb"
$desktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "AstroLabb.lnk"
$exePath = Join-Path $installDir "AstroLabb.exe"
$uninstallCmdPath = Join-Path $installDir "Uninstall-AstroLabb.cmd"

if (-not (Test-Path $payloadTar)) {
    throw "Installer payload not found: $payloadTar"
}

Get-Process AstroLabb -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

if (Test-Path $installDir) {
    Remove-Item -LiteralPath $installDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null
& tar -xf $payloadTar -C $installDir
if ($LASTEXITCODE -ne 0) {
    throw "Payload extraction failed with exit code $LASTEXITCODE."
}
Copy-Item (Join-Path $packageRoot "uninstall.cmd") $uninstallCmdPath -Force

$wsh = New-Object -ComObject WScript.Shell

$appShortcut = $wsh.CreateShortcut((Join-Path $startMenuDir "AstroLabb.lnk"))
$appShortcut.TargetPath = $exePath
$appShortcut.WorkingDirectory = $installDir
$appShortcut.Save()

$uninstallShortcut = $wsh.CreateShortcut((Join-Path $startMenuDir "Uninstall AstroLabb.lnk"))
$uninstallShortcut.TargetPath = $uninstallCmdPath
$uninstallShortcut.WorkingDirectory = $installDir
$uninstallShortcut.Save()

$desktopShortcut = $wsh.CreateShortcut($desktopShortcutPath)
$desktopShortcut.TargetPath = $exePath
$desktopShortcut.WorkingDirectory = $installDir
$desktopShortcut.Save()

if (-not $Quiet) {
    Start-Process -FilePath $exePath -WorkingDirectory $installDir
}

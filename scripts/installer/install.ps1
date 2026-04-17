param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$packageRoot = $PSScriptRoot
$payloadZip = Join-Path $packageRoot "AstroLabb-payload.zip"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\AstroLabb"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\AstroLabb"
$desktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "AstroLabb.lnk"
$exePath = Join-Path $installDir "AstroLabb.exe"
$uninstallCmdPath = Join-Path $installDir "Uninstall-AstroLabb.cmd"

if (-not (Test-Path $payloadZip)) {
    throw "Installer payload not found: $payloadZip"
}

if (Test-Path $installDir) {
    Remove-Item -LiteralPath $installDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null
Expand-Archive -Path $payloadZip -DestinationPath $installDir -Force
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

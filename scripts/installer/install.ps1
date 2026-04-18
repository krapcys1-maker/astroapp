param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Resolve-InstallDir {
    param(
        [string]$DefaultInstallDir
    )

    if ($Quiet) {
        return $DefaultInstallDir
    }

    Add-Type -AssemblyName System.Windows.Forms

    $defaultParent = Split-Path $DefaultInstallDir -Parent
    $choice = [System.Windows.Forms.MessageBox]::Show(
        "AstroLabb can be installed in the default folder:`n`n$DefaultInstallDir`n`nChoose 'Yes' to use it, 'No' to pick another folder, or 'Cancel' to stop installation.",
        "AstroLabb Setup",
        [System.Windows.Forms.MessageBoxButtons]::YesNoCancel,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )

    if ($choice -eq [System.Windows.Forms.DialogResult]::Cancel) {
        throw "Installation cancelled by user."
    }

    if ($choice -eq [System.Windows.Forms.DialogResult]::Yes) {
        return $DefaultInstallDir
    }

    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Choose the parent folder for AstroLabb. The installer will create an 'AstroLabb' subfolder there."
    $dialog.UseDescriptionForTitle = $true
    $dialog.ShowNewFolderButton = $true
    $dialog.SelectedPath = $defaultParent

    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw "Installation cancelled by user."
    }

    return Join-Path $dialog.SelectedPath "AstroLabb"
}

$packageRoot = $PSScriptRoot
$payloadTar = Join-Path $packageRoot "AstroLabb-payload.tar"
$defaultInstallDir = Join-Path $env:LOCALAPPDATA "Programs\AstroLabb"
$installDir = Resolve-InstallDir -DefaultInstallDir $defaultInstallDir
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
    [System.Windows.Forms.MessageBox]::Show(
        "AstroLabb was installed to:`n`n$installDir",
        "AstroLabb Setup",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
    Start-Process -FilePath $exePath -WorkingDirectory $installDir
}

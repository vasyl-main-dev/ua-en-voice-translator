param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("online", "offline")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if ($env:OS -ne "Windows_NT") {
    throw "Windows installers must be built on Windows."
}

python -m pip install -r requirements-cpu.txt -r requirements-build.txt

if ($Mode -eq "offline") {
    python scripts/download_offline_models.py `
        --output build/offline_models
}

$env:VOICE_TRANSLATOR_PACKAGE_MODE = $Mode
python -m PyInstaller `
    --noconfirm `
    --clean `
    packaging/voice_translator.spec

$InnoSetupCompiler = Join-Path `
    ${env:ProgramFiles(x86)} `
    "Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetupCompiler)) {
    throw "Inno Setup 6 was not found: $InnoSetupCompiler"
}

& $InnoSetupCompiler `
    "/DPackageMode=$Mode" `
    "packaging\windows_installer.iss"

Write-Host "Installer created in installer_output"


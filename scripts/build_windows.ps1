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
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed with exit code $LASTEXITCODE."
}

if ($Mode -eq "offline") {
    python scripts/download_offline_models.py `
        --output build/offline_models
    if ($LASTEXITCODE -ne 0) {
        throw "Offline model download failed with exit code $LASTEXITCODE."
    }
}

$env:VOICE_TRANSLATOR_PACKAGE_MODE = $Mode
python -m PyInstaller `
    --noconfirm `
    --clean `
    packaging/voice_translator.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

$InnoSetupCompiler = Join-Path `
    ${env:ProgramFiles(x86)} `
    "Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetupCompiler)) {
    throw "Inno Setup 6 was not found: $InnoSetupCompiler"
}

& $InnoSetupCompiler `
    "/DPackageMode=$Mode" `
    "packaging\windows_installer.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}

Write-Host "Installer created in installer_output"

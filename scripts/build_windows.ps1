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

$ApplicationDirectoryName = if ($Mode -eq "offline") {
    "UA-EN-Voice-Translator-Offline"
} else {
    "UA-EN-Voice-Translator-Online"
}
$ApplicationExecutable = Join-Path `
    $ProjectRoot `
    "dist\$ApplicationDirectoryName\$ApplicationDirectoryName.exe"

# Deliberately request CUDA. The universal build's runtime hook must override
# it before application imports and still report a healthy CPU profile.
$env:VOICE_TRANSLATOR_DEVICE = "cuda"
& $ApplicationExecutable --runtime-check
if ($LASTEXITCODE -ne 0) {
    throw "Packaged CPU runtime check failed with exit code $LASTEXITCODE."
}
Remove-Item Env:VOICE_TRANSLATOR_DEVICE -ErrorAction SilentlyContinue

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

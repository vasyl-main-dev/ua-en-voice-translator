param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "online",
        "offline",
        "nvidia-large-online",
        "nvidia-large-offline"
    )]
    [string]$Mode
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if ($env:OS -ne "Windows_NT") {
    throw "Windows installers must be built on Windows."
}

$IsNvidiaPackage = $Mode.StartsWith("nvidia-large-")
$IsOfflinePackage = $Mode.EndsWith("offline")
$SpeechModel = if ($IsNvidiaPackage) { "large-v3" } else { "medium" }
$RuntimeRequirements = if ($IsNvidiaPackage) {
    "requirements-nvidia.txt"
} else {
    "requirements-cpu.txt"
}

python -m pip install -r $RuntimeRequirements -r requirements-build.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed with exit code $LASTEXITCODE."
}

if ($IsOfflinePackage) {
    python scripts/download_offline_models.py `
        --output build/offline_models `
        --speech-model $SpeechModel
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

$ApplicationDirectoryNames = @{
    "online" = "UA-EN-Voice-Translator-Online"
    "offline" = "UA-EN-Voice-Translator-Offline"
    "nvidia-large-online" = "UA-EN-Voice-Translator-NVIDIA-Large-Online"
    "nvidia-large-offline" = "UA-EN-Voice-Translator-NVIDIA-Large-Offline"
}
$ApplicationDirectoryName = $ApplicationDirectoryNames[$Mode]
$ApplicationExecutable = Join-Path `
    $ProjectRoot `
    "dist\$ApplicationDirectoryName\$ApplicationDirectoryName.exe"

# GitHub's hosted Windows runner has no NVIDIA GPU. Universal packages can be
# fully runtime-checked there; NVIDIA packages receive a metadata/import smoke
# check and are then tested manually on real discrete GPUs.
if ($IsNvidiaPackage) {
    $env:VOICE_TRANSLATOR_DEVICE = "cpu"
    & $ApplicationExecutable --package-check
    if ($LASTEXITCODE -ne 0) {
        throw "Packaged NVIDIA metadata check failed with exit code $LASTEXITCODE."
    }
} else {
    $env:VOICE_TRANSLATOR_DEVICE = "cuda"
    & $ApplicationExecutable --runtime-check
    if ($LASTEXITCODE -ne 0) {
        throw "Packaged CPU runtime check failed with exit code $LASTEXITCODE."
    }
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

#ifndef PackageMode
  #define PackageMode "online"
#endif

#if PackageMode == "nvidia-large-offline"
  #define ApplicationName "UA-EN Voice Translator NVIDIA Large Offline"
  #define ExecutableName "UA-EN-Voice-Translator-NVIDIA-Large-Offline.exe"
  #define SourceDirectory "UA-EN-Voice-Translator-NVIDIA-Large-Offline"
  #define ApplicationId "{{D24E4B84-8C1C-4B93-8E5C-843378B0F37B}"
#elif PackageMode == "nvidia-large-online"
  #define ApplicationName "UA-EN Voice Translator NVIDIA Large Online"
  #define ExecutableName "UA-EN-Voice-Translator-NVIDIA-Large-Online.exe"
  #define SourceDirectory "UA-EN-Voice-Translator-NVIDIA-Large-Online"
  #define ApplicationId "{{64B36E31-C86F-4FC0-92E5-E17239D992E1}"
#elif PackageMode == "offline"
  #define ApplicationName "UA-EN Voice Translator Offline"
  #define ExecutableName "UA-EN-Voice-Translator-Offline.exe"
  #define SourceDirectory "UA-EN-Voice-Translator-Offline"
  #define ApplicationId "{{D95E2505-2220-47C6-BFA1-B67159105653}"
#else
  #define ApplicationName "UA-EN Voice Translator Online"
  #define ExecutableName "UA-EN-Voice-Translator-Online.exe"
  #define SourceDirectory "UA-EN-Voice-Translator-Online"
  #define ApplicationId "{{E84BF8C9-D9E2-46F8-9256-E6741A5CE978}"
#endif

#if PackageMode == "nvidia-large-offline" || PackageMode == "nvidia-large-online"
  #define ApplicationVersion "0.4.0-beta.1"
#else
  #define ApplicationVersion "0.3.0"
#endif
#define PublisherName "UA-EN Voice Translator"

[Setup]
AppId={#ApplicationId}
AppName={#ApplicationName}
AppVersion={#ApplicationVersion}
AppPublisher={#PublisherName}
DefaultDirName={localappdata}\Programs\UA-EN Voice Translator\{#PackageMode}
DefaultGroupName=UA-EN Voice Translator
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\installer_output
OutputBaseFilename=UA-EN-Voice-Translator-{#PackageMode}-Setup-{#ApplicationVersion}
#if PackageMode == "offline" || PackageMode == "nvidia-large-offline"
Compression=lzma2/fast
SolidCompression=no
#else
Compression=lzma2/ultra64
SolidCompression=yes
#endif
#if PackageMode == "nvidia-large-offline"
DiskSpanning=yes
SlicesPerDisk=1
DiskSliceSize=1900000000
#endif
WizardStyle=modern
UninstallDisplayIcon={app}\{#ExecutableName}

[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\{#SourceDirectory}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#ApplicationName}"; Filename: "{app}\{#ExecutableName}"
Name: "{autodesktop}\{#ApplicationName}"; Filename: "{app}\{#ExecutableName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Створити ярлик на робочому столі"; GroupDescription: "Додаткові ярлики:"

[Run]
Filename: "{app}\{#ExecutableName}"; Description: "Запустити {#ApplicationName}"; Flags: nowait postinstall skipifsilent

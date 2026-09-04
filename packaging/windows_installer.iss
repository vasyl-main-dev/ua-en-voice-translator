#ifndef PackageMode
  #define PackageMode "online"
#endif

#if PackageMode == "offline"
  #define ApplicationName "UA-EN Voice Translator Offline"
  #define ExecutableName "UA-EN-Voice-Translator-Offline.exe"
  #define SourceDirectory "UA-EN-Voice-Translator-Offline"
#else
  #define ApplicationName "UA-EN Voice Translator Online"
  #define ExecutableName "UA-EN-Voice-Translator-Online.exe"
  #define SourceDirectory "UA-EN-Voice-Translator-Online"
#endif

#define ApplicationVersion "0.3.0"
#define PublisherName "UA-EN Voice Translator"

[Setup]
AppId={{D95E2505-2220-47C6-BFA1-B67159105653}
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
Compression=lzma2/ultra64
SolidCompression=yes
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


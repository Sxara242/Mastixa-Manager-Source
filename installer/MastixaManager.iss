#define MyAppName "Mastixa Manager"
#define MyAppVersion "0.40.0-alpha.1"
#define MyAppExeName "MastixaManager.exe"

[Setup]
AppId={{B9B946A2-8711-4B35-9BCB-B40210E67357}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=Mastixa Manager
DefaultDirName={%LOCALAPPDATA}\Programs\Mastixa Manager
DefaultGroupName=Mastixa Manager
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\installer
OutputBaseFilename=MastixaManager-{#MyAppVersion}-Setup
SetupIconFile=..\packaging\mastixa_manager.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=0.40.0.1
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=0.40.0.1

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\MastixaManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Mastixa Manager"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Mastixa Manager"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Mastixa Manager}"; Flags: nowait postinstall skipifsilent

#define MyAppName "Mastixa Manager"
#define MyAppVersion "1.0.0-rc.2"
#define MyAppExeName "MastixaManager.exe"
#ifndef MyAppSourceDir
  #define MyAppSourceDir "..\dist\MastixaManager"
#endif

[Setup]
AppId={{B9B946A2-8711-4B35-9BCB-B40210E67357}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=Mastixa Manager
LicenseFile=..\LICENSE
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
VersionInfoVersion=1.0.0.2
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.0.0.2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Mastixa Manager"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Mastixa Manager"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Application preferences are user-scoped and should not survive an explicit uninstall.
; Keep the parent Mastixa key only when another Mastixa application still uses it.
Root: HKCU; Subkey: "Software\Mastixa"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Mastixa\Mastixa Manager"; Flags: uninsdeletekey

[UninstallDelete]
; The install directory is dedicated to Mastixa Manager. Remove any runtime/build residue
; that was created inside it but was not tracked as an installed file by Inno Setup.
; User databases, profiles and backups live separately under %LOCALAPPDATA%\MastixaManager
; and are preserved by default unless the user explicitly requests a full data purge.
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Mastixa Manager}"; Flags: nowait postinstall skipifsilent

[Code]
#include "vc_redist_prerequisite.iss"

function InitializeSetup: Boolean;
begin
  Result := VcRedistPrerequisiteReady;
  if not Result then
    MsgBox(VcRedistPrerequisiteMessage, mbError, MB_OK);
end;

const
  MastixaUninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B9B946A2-8711-4B35-9BCB-B40210E67357}_is1';

var
  DeleteUserDataOnUninstall: Boolean;
  ExistingInstallDetected: Boolean;
  InstalledVersion: String;
  MaintenanceMode: String;
  MaintenancePage: TInputOptionWizardPage;

function CmdLineParamExists(const Value: string): Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), Value) = 0 then
    begin
      Result := True;
      Exit;
    end;
end;

procedure InitializeWizard;
var
  CurrentVersion: String;
begin
  CurrentVersion := '{#MyAppVersion}';
  ExistingInstallDetected := RegKeyExists(HKCU, MastixaUninstallKey);
  InstalledVersion := '';
  MaintenanceMode := 'install';

  if not ExistingInstallDetected then
    Exit;

  if not RegQueryStringValue(
    HKCU,
    MastixaUninstallKey,
    'DisplayVersion',
    InstalledVersion) then
  begin
    InstalledVersion := 'unknown';
  end;

  if CompareText(InstalledVersion, CurrentVersion) = 0 then
  begin
    MaintenanceMode := 'repair';
    MaintenancePage := CreateInputOptionPage(
      wpWelcome,
      'Existing installation detected',
      'Mastixa Manager ' + CurrentVersion + ' is already installed.',
      'Choose Fix / repair installation to restore the application files and shortcuts. ' +
      'Your local database, profiles, documents, logs and backups will be kept.',
      True,
      False);
    MaintenancePage.Add('Fix / repair installation (recommended)');
    MaintenancePage.SelectedValueIndex := 0;
  end
  else
  begin
    MaintenanceMode := 'update';
    MaintenancePage := CreateInputOptionPage(
      wpWelcome,
      'Existing installation detected',
      'Installed version: ' + InstalledVersion + '    Installer version: ' + CurrentVersion,
      'Choose Update program to replace the application files with this version. ' +
      'Your local database, profiles, documents, logs and backups will be kept.',
      True,
      False);
    MaintenancePage.Add('Update program to ' + CurrentVersion + ' (recommended)');
    MaintenancePage.SelectedValueIndex := 0;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  if ExistingInstallDetected then
    Log(
      'Existing Mastixa Manager installation detected. Mode=' + MaintenanceMode +
      '; installed=' + InstalledVersion + '; target={#MyAppVersion}');
  Result := '';
end;

function IsSilentUninstall: Boolean;
begin
  Result := CmdLineParamExists('/SILENT') or CmdLineParamExists('/VERYSILENT');
end;

function InitializeUninstall: Boolean;
begin
  { Safe default: keep user data. Explicit /PURGEDATA also supports scripted cleanup. }
  DeleteUserDataOnUninstall := CmdLineParamExists('/PURGEDATA');

  if (not DeleteUserDataOnUninstall) and (not IsSilentUninstall) then
  begin
    DeleteUserDataOnUninstall :=
      SuppressibleMsgBox(
        'Do you also want to permanently delete all Mastixa Manager local data, profiles, documents, logs and backups?' + #13#10 + #13#10 +
        'Choose No to keep your data for a reinstall or upgrade.',
        mbConfirmation,
        MB_YESNO or MB_DEFBUTTON2,
        IDNO) = IDYES;
  end;

  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataDir: String;
begin
  if (CurUninstallStep = usPostUninstall) and DeleteUserDataOnUninstall then
  begin
    UserDataDir := ExpandConstant('{localappdata}\MastixaManager');
    if DirExists(UserDataDir) then
    begin
      Log('Full uninstall requested. Removing user data: ' + UserDataDir);
      if not DelTree(UserDataDir, True, True, True) then
        Log('Warning: some Mastixa Manager user data could not be removed.');
    end;
  end;
end;

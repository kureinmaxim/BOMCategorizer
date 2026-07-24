#define MyAppVersion "3.3.0"
#define MyAppEdition "Standard"
#define MyAppPublisher "Kurein M.N."
; Стабильный AppId — при установке новой версии старая тихо удаляется, затем ставится новая.
; Персональные config/БД сохраняются (см. PreserveUserData / RestoreUserData).
#define MyAppId "{{E8F2A91B-4C7D-4E5A-9B2F-A1B2C3D4E5F7}}"

[Setup]
AppId={#MyAppId}
AppName=BOM Categorizer Standard
AppVersion={#MyAppVersion}
AppVerName=BOM Categorizer {#MyAppEdition} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/kureinmaxim/BOMCategorizer
AppSupportURL=https://github.com/kureinmaxim/BOMCategorizer/issues
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=BOM Categorizer - Bill of Materials Categorization Tool
VersionInfoProductName=BOM Categorizer {#MyAppEdition}
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={userappdata}\BOMCategorizer
DefaultGroupName=BOM Categorizer Standard
DisableDirPage=auto
UsePreviousAppDir=yes
UsePreviousGroup=yes
OutputDir=.
OutputBaseFilename=BOMCategorizerSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
CloseApplications=yes
RestartIfNeededByRun=yes
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName=BOM Categorizer {#MyAppEdition} v{#MyAppVersion}
WizardStyle=modern

[Files]
Source: "temp_installer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__"
Source: "temp_installer\fonts\*.ttf"; DestDir: "{app}\fonts"; Flags: ignoreversion; Check: FontsExist

[Run]
Filename: "{sysnative}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\post_install.ps1"""; StatusMsg: "Setting up Python environment..."; Flags: runhidden

[Icons]
Name: "{group}\BOM Categorizer Standard"; Filename: "{app}\scripts\run_app.bat"; WorkingDir: "{app}\scripts"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall BOM Categorizer Standard"; Filename: "{uninstallexe}"
Name: "{userdesktop}\BOM Categorizer Standard"; Filename: "{app}\scripts\run_app.bat"; WorkingDir: "{app}\scripts"; IconFilename: "{app}\assets\icon.ico"

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

procedure PreserveUserData();
var
  AppDir, BackupDir: String;
  Dummy: Integer;
begin
  AppDir := ExpandConstant('{userappdata}\BOMCategorizer');
  BackupDir := ExpandConstant('{tmp}\BOMCategorizer_userdata');
  if DirExists(BackupDir) then
    DelTree(BackupDir, True, True, True);
  ForceDirectories(BackupDir);
  if FileExists(AppDir + '\config.json') then
    FileCopy(AppDir + '\config.json', BackupDir + '\config.json', False);
  if FileExists(AppDir + '\component_database.json') then
    FileCopy(AppDir + '\component_database.json', BackupDir + '\component_database.json', False);
  if DirExists(AppDir + '\Data') then
    Exec('cmd.exe', '/C xcopy /E /I /Y "' + AppDir + '\Data" "' + BackupDir + '\Data"', '', SW_HIDE, ewWaitUntilTerminated, Dummy);
end;

procedure RestoreUserData();
var
  AppDir, BackupDir: String;
  Dummy: Integer;
begin
  AppDir := ExpandConstant('{app}');
  BackupDir := ExpandConstant('{tmp}\BOMCategorizer_userdata');
  if FileExists(BackupDir + '\config.json') then
    FileCopy(BackupDir + '\config.json', AppDir + '\config.json', False);
  if FileExists(BackupDir + '\component_database.json') then
    FileCopy(BackupDir + '\component_database.json', AppDir + '\component_database.json', False);
  if DirExists(BackupDir + '\Data') then
    Exec('cmd.exe', '/C xcopy /E /I /Y "' + BackupDir + '\Data" "' + AppDir + '\Data"', '', SW_HIDE, ewWaitUntilTerminated, Dummy);
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    PreserveUserData();
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  Exec('taskkill', '/F /IM python.exe /FI "WINDOWTITLE eq BOM*"', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Exec('taskkill', '/F /IM pythonw.exe /FI "WINDOWTITLE eq BOM*"', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Exec('taskkill', '/F /IM run_app.bat', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Result := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  NeedsRestart := False;
  if IsUpgrade() then
    UnInstallOldVersion();
  Result := '';
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    RestoreUserData();
end;

function FontsExist: Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\temp_installer\fonts'));
end;

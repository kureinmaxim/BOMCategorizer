#define MyAppVersion "5.6.2"
#define MyAppEdition "Modern Edition"
#define MyAppPublisher "Kurein M.N."
[Setup]
AppName=BOM Categorizer Modern Edition
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
DefaultDirName={userappdata}\BOMCategorizerModern
DefaultGroupName=BOM Categorizer Modern Edition
OutputDir=.
OutputBaseFilename=BOMCategorizerModernSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
CloseApplications=yes
RestartIfNeededByRun=yes
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName=BOM Categorizer {#MyAppEdition} v{#MyAppVersion}

[Files]
Source: "temp_installer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__"
Source: "temp_installer\fonts\*.ttf"; DestDir: "{app}\fonts"; Flags: ignoreversion; Check: FontsExist

[Run]
Filename: "{sysnative}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\post_install.ps1"""; StatusMsg: "Setting up Python environment..."; Flags: runhidden

[Icons]
Name: "{group}\BOM Categorizer Modern"; Filename: "{app}\scripts\run_app.bat"; WorkingDir: "{app}\scripts"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall BOM Categorizer Modern"; Filename: "{uninstallexe}"
Name: "{userdesktop}\BOM Categorizer Modern"; Filename: "{app}\scripts\run_app.bat"; WorkingDir: "{app}\scripts"; IconFilename: "{app}\assets\icon.ico"

[Code]
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  // Закрываем процессы приложения, если они запущены
  // Это предотвращает ошибку "Access is denied" при замене файлов
  Exec('taskkill', '/F /IM python.exe /FI "WINDOWTITLE eq BOM*"', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Exec('taskkill', '/F /IM run_app.bat', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Result := True;
end;

function FontsExist: Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\temp_installer\fonts'));
end;


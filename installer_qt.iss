#define MyAppVersion "4.3.7"
#define MyAppEdition "Modern Edition"
[Setup]
AppName=BOM Categorizer Modern Edition
AppVersion={#MyAppVersion}
DefaultDirName={userappdata}\BOMCategorizerModern
DefaultGroupName=BOM Categorizer Modern Edition
OutputDir=.
OutputBaseFilename=BOMCategorizerModernSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico

[Files]
Source: "temp_installer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__"
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\fonts\*.ttf"; DestDir: "{app}\fonts"; Flags: ignoreversion; Check: FontsExist

[Run]
Filename: "{sysnative}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\post_install.ps1"""; StatusMsg: "Setting up Python environment..."; Flags: runhidden

[Icons]
Name: "{group}\BOM Categorizer Modern"; Filename: "{app}\run_app.bat"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall BOM Categorizer Modern"; Filename: "{uninstallexe}"
Name: "{userdesktop}\BOM Categorizer Modern"; Filename: "{app}\run_app.bat"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"

[Code]
function FontsExist: Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\temp_installer\fonts'));
end;


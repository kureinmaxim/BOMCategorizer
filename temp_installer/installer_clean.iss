#define MyAppVersion "2.0.34"
[Setup]
AppName=BOM Categorizer
AppVersion={#MyAppVersion}
DefaultDirName={userappdata}\BOMCategorizer
DefaultGroupName=BOM Categorizer
OutputDir=.
OutputBaseFilename=BOMCategorizerSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "temp_installer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__"

[Run]
Filename: "{sysnative}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\post_install.ps1"""; StatusMsg: "Setting up Python environment..."; Flags: runhidden

[Icons]
Name: "{group}\BOM Categorizer"; Filename: "{app}\run_app.bat"; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 2
Name: "{group}\Uninstall BOM Categorizer"; Filename: "{uninstallexe}"
Name: "{userdesktop}\BOM Categorizer"; Filename: "{app}\run_app.bat"; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 2

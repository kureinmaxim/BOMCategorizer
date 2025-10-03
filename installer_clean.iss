#define MyAppVersion "1.0.4"
[Setup]
AppName=BOM Categorizer
AppVersion={#MyAppVersion}
DefaultDirName={pf64}\BOMCategorizer
DefaultGroupName=BOM Categorizer
OutputDir=.
OutputBaseFilename=BOMCategorizerSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "temp_installer\app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\split_bom.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\BUILD.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\interactive_classify.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\post_install.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\preview_unclassified.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\rules.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "temp_installer\run_app.bat"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "{sysnative}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\post_install.ps1"""; StatusMsg: "Setting up Python environment..."; Flags: runhidden

[Icons]
Name: "{group}\BOM Categorizer"; Filename: "{app}\run_app.bat"; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 2
Name: "{group}\Uninstall BOM Categorizer"; Filename: "{uninstallexe}"

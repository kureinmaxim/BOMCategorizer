[Setup]
AppName=BOM Categorizer
AppVersion={#GetFileVersion}
DefaultDirName={pf64}\BOMCategorizer
DefaultGroupName=BOM Categorizer
OutputDir=.
OutputBaseFilename=BOMCategorizerSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
; Read version from config.json
#define GetFileVersion \
  ( \
    Local[0] = GetFileContents('config.json'), \
    Local[1] = Pos('"version"', Local[0]), \
    (Local[1] > 0) ? \
      Copy(Local[0], Pos('"', Local[0], Local[1] + 9) + 1, \
           Pos('"', Local[0], Pos('"', Local[0], Local[1] + 9) + 1) - (Pos('"', Local[0], Local[1] + 9) + 1)) \
      : '1.0.0' \
  )

[Files]
Source: "app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "split_bom.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "*"; Excludes: ".venv\*;out\*;out_*\*;__pycache__\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "post_install.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "powershell"; Parameters: "-ExecutionPolicy Bypass -File \"{app}\\post_install.ps1\""; StatusMsg: "Setting up Python environment..."; Flags: runhidden

[Icons]
Name: "{group}\BOM Categorizer"; Filename: "{app}\\.venv\\Scripts\\python.exe"; Parameters: "\"{app}\\app.py\""; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 2
Name: "{group}\Uninstall BOM Categorizer"; Filename: "{uninstallexe}"



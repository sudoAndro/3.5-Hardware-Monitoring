; SPDX-License-Identifier: GPL-3.0-or-later
; Inno-Setup-Skript fuer den sudoAndro Hardware-Monitoring Installer.
; Baut einen eigenstaendigen Setup.exe: kein Python/pip noetig, richtet Autostart +
; Display-Aus-Aufgaben ein, installiert optional PawnIO, legt Verknuepfungen an.
; Kompilieren:  ISCC.exe install\sudoAndro-installer.iss   (aus dem Projekt-Root)

#define AppName "3,5-Zoll Hardware-Monitoring"
#define AppVer "1.0"
#define AppPublisher "sudoAndro"
#define AppURL "https://github.com/sudoAndro/3.5-Hardware-Monitoring"
#define AppExe "sudoAndro-Studio.exe"

[Setup]
AppId={{A1D0C7E2-3B4F-4E8A-9C1D-53DA4F5E6B70}
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\sudoAndro Hardware-Monitoring
DefaultGroupName=sudoAndro Hardware-Monitoring
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=..\dist-installer
OutputBaseFilename=sudoAndro-Setup-v{#AppVer}
SetupIconFile=..\res\themes\sudoAndro\sudoandro.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "pawnio"; Description: "PawnIO-Treiber installieren (fuer CPU-Temperatur - empfohlen)"; GroupDescription: "Treiber:"

[Files]
Source: "..\sudoAndro-Monitor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\sudoAndro-Studio.exe";  DestDir: "{app}"; Flags: ignoreversion
Source: "..\display-off.exe";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\config.example.yaml";   DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md";             DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\LICENSE";               DestDir: "{app}"; Flags: ignoreversion
Source: "register-tasks.ps1";         DestDir: "{app}\install"; Flags: ignoreversion
Source: "remove-tasks-installed.ps1"; DestDir: "{app}\install"; Flags: ignoreversion
Source: "..\res\*";      DestDir: "{app}\res";      Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\external\*"; DestDir: "{app}\external"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Standardnutzer duerfen im Programmordner schreiben (Themes bearbeiten, config.yaml,
; Wettersymbol-Cache) - sonst koennte das Studio nichts speichern
Name: "{app}"; Permissions: users-modify

[Icons]
Name: "{group}\sudoAndro Studio"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\res\themes\sudoAndro\sudoandro.ico"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\sudoAndro Studio"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\res\themes\sudoAndro\sudoandro.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\external\PawnIO\PawnIO_setup.exe"; Parameters: "-install -silent"; StatusMsg: "PawnIO-Treiber wird installiert..."; Tasks: pawnio; Flags: waituntilterminated runascurrentuser
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\register-tasks.ps1"" -AppDir ""{app}"" -TaskUser ""{username}"""; StatusMsg: "Autostart und Display-Aus werden eingerichtet..."; Flags: runhidden waituntilterminated
Filename: "{app}\{#AppExe}"; Description: "sudoAndro Studio jetzt starten"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\remove-tasks-installed.ps1"""; Flags: runhidden waituntilterminated; RunOnceId: "RemoveTuringTasks"

[Code]
// Vor der Installation laufende Aufgaben/Prozesse stoppen (fuer saubere Updates)
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    Exec('schtasks.exe', '/end /tn "TuringSmartScreen"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/f /im sudoAndro-Monitor.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/f /im sudoAndro-Studio.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

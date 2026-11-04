; Inno Setup Script for Vitalcer Store System
; Produces a self-contained, single-file installer (vitalcer-setup-x64.exe)

#define MyAppName "Vitalcer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Vitalcer Dietética"
#define MyAppURL "https://github.com/brianmatozo/vit-try2"
#define MyAppExeName "vitalcer.exe"

[Setup]
AppId={{8B036D81-0676-4F28-86A6-928E1012C573}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName=C:\Vitalcer
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\..\dist
OutputBaseFilename=vitalcer-setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
WizardStyle=modern
DisableWelcomePage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "posdesktopicon"; Description: "Crear acceso directo a Vitalcer POS (Caja) en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked=false
Name: "admindesktopicon"; Description: "Crear acceso directo a Vitalcer Admin en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked=false
Name: "autostart"; Description: "Iniciar Vitalcer automáticamente en segundo plano al encender la computadora"; GroupDescription: "Inicio del sistema:"; Flags: unchecked=false

[Files]
; 1. PyInstaller bundled backend & headless launcher
Source: "..\..\dist\vitalcer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. Caddy web server & config
Source: "..\..\tools\caddy\caddy.exe"; DestDir: "{app}\tools\caddy"; Flags: ignoreversion
Source: "..\..\Caddyfile"; DestDir: "{app}"; Flags: ignoreversion

; 3. PostgreSQL portable binaries
Source: "..\..\tools\pgsql\*"; DestDir: "{app}\tools\pgsql"; Flags: ignoreversion recursesubdirs createallsubdirs

; 4. Pre-built static SPAs (Admin & POS)
Source: "..\..\apps\admin\build\*"; DestDir: "{app}\apps\admin\build"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\apps\pos\build\*"; DestDir: "{app}\apps\pos\build"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\data\postgres"; Permissions: users-full
Name: "{app}\data\logs"; Permissions: users-full

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Vitalcer"; ValueData: """{app}\{#MyAppExeName}"" --startup"; Flags: uninsdeletevalue; Tasks: autostart

[Icons]
Name: "{autodesktop}\Vitalcer POS"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--pos"; WorkingDir: "{app}"; Tasks: posdesktopicon
Name: "{autodesktop}\Vitalcer Admin"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--admin"; WorkingDir: "{app}"; Tasks: admindesktopicon
Name: "{group}\Vitalcer POS (Caja)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--pos"; WorkingDir: "{app}"
Name: "{group}\Vitalcer Admin"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--admin"; WorkingDir: "{app}"
Name: "{group}\Detener Servicios Vitalcer"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--stop"; WorkingDir: "{app}"
Name: "{group}\Desinstalar Vitalcer"; Filename: "{uninstallexe}"

[Run]
; Database cluster initialization (only on clean install)
Filename: "{app}\tools\pgsql\bin\initdb.exe"; Parameters: "-D ""{app}\data\postgres"" -U vitalcer --auth=trust --encoding=UTF8"; StatusMsg: "Inicializando base de datos local..."; Flags: runhidden waituntilterminated; Check: NeedsDbInit

; Database creation
Filename: "{app}\tools\pgsql\bin\pg_ctl.exe"; Parameters: "-D ""{app}\data\postgres"" -l ""{app}\data\logs\postgres.log"" -w start"; StatusMsg: "Configurando tablas y catálogo..."; Flags: runhidden waituntilterminated; Check: NeedsDbInit
Filename: "{app}\tools\pgsql\bin\createdb.exe"; Parameters: "-U vitalcer -h 127.0.0.1 vitalcer"; Flags: runhidden waituntilterminated; Check: NeedsDbInit
Filename: "{app}\tools\pgsql\bin\pg_ctl.exe"; Parameters: "-D ""{app}\data\postgres"" -m fast stop"; Flags: runhidden waituntilterminated; Check: NeedsDbInit

; Post-install launch action
Filename: "{app}\{#MyAppExeName}"; Parameters: "--pos"; Description: "Abrir Vitalcer POS ahora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--stop"; Flags: runhidden; RunOnceId: "StopServices"
Filename: "{app}\tools\pgsql\bin\pg_ctl.exe"; Parameters: "-D ""{app}\data\postgres"" -m fast stop"; Flags: runhidden; RunOnceId: "StopPostgres"
Filename: "taskkill.exe"; Parameters: "/F /IM caddy.exe"; Flags: runhidden; RunOnceId: "KillCaddy"
Filename: "taskkill.exe"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillVitalcer"

[Code]
function NeedsDbInit(): Boolean;
begin
  Result := not FileExists(ExpandConstant('{app}\data\postgres\PG_VERSION'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    if DirExists(ExpandConstant('{app}\data\postgres')) then
    begin
      if MsgBox('¿Deseas conservar la base de datos y el catálogo de productos existente en data\postgres?', mbConfirmation, MB_YESNO) = IDNO then
      begin
        DelTree(ExpandConstant('{app}\data'), True, True, True);
      end;
    end;
  end;
end;

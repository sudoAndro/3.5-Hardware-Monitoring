# SPDX-License-Identifier: GPL-3.0-or-later
# register-tasks.ps1: Wird vom Installer (Inno Setup, bereits mit Adminrechten) aufgerufen.
# Registriert die beiden geplanten Aufgaben, die auf die INSTALLIERTEN Exes zeigen.
# Bekommt Installationsordner und Benutzer als Parameter (keine Abhaengigkeit von
# Umgebungsvariablen, die bei Elevation falsch sein koennten).
param(
    [Parameter(Mandatory = $true)][string]$AppDir,
    [Parameter(Mandatory = $true)][string]$TaskUser
)

$ErrorActionPreference = "Stop"
$monitorExe = Join-Path $AppDir "sudoAndro-Monitor.exe"
$offExe = Join-Path $AppDir "display-off.exe"

# Benutzer ggf. mit Computername qualifizieren (Installer uebergibt nur den Namen)
if ($TaskUser -notmatch '\\') { $TaskUser = "$env:COMPUTERNAME\$TaskUser" }

# ---- config.yaml aus Vorlage erzeugen (falls noch nicht vorhanden) ----
$cfg = Join-Path $AppDir "config.yaml"
if (-not (Test-Path $cfg)) {
    Copy-Item (Join-Path $AppDir "config.example.yaml") $cfg
}

# ---- Aufgabe 1: Monitor-Autostart bei Anmeldung ----
$action = New-ScheduledTaskAction -Execute $monitorExe -WorkingDirectory $AppDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $TaskUser
$principal = New-ScheduledTaskPrincipal -UserId $TaskUser -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "TuringSmartScreen" -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

# ---- Aufgabe 2: Display-Aus bei Abmeldung/Herunterfahren (laeuft als SYSTEM) ----
$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Schaltet das Display bei Abmeldung/Herunterfahren aus (sudoAndro)</Description>
  </RegistrationInfo>
  <Triggers>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="System"&gt;&lt;Select Path="System"&gt;*[System[Provider[@Name='Microsoft-Windows-Winlogon'] and EventID=7002]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="System"&gt;&lt;Select Path="System"&gt;*[System[Provider[@Name='User32'] and EventID=1074]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <AllowStartOnDemand>true</AllowStartOnDemand>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$offExe</Command>
      <WorkingDirectory>$AppDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
$xmlPath = Join-Path $env:TEMP "TuringDisplayOff.xml"
$xml | Out-File -FilePath $xmlPath -Encoding Unicode
schtasks /create /f /tn "TuringDisplayOff" /xml $xmlPath | Out-Null
Remove-Item $xmlPath -ErrorAction SilentlyContinue

# ---- Monitor sofort starten ----
Start-ScheduledTask -TaskName "TuringSmartScreen"

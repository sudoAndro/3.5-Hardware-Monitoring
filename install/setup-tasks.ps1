# SPDX-License-Identifier: GPL-3.0-or-later
# setup-tasks.ps1: Richtet die beiden geplanten Aufgaben ein:
#   TuringSmartScreen - startet den Display-Monitor bei jeder Anmeldung (mit Adminrechten,
#                       noetig fuer die CPU-Temperatur via LibreHardwareMonitor)
#   TuringDisplayOff  - schaltet das Display bei Abmeldung/Herunterfahren aus
#                       (laeuft als SYSTEM, reagiert auf Windows-Ereignisse 7002/1074)
#
# Aufruf: Rechtsklick > "Mit PowerShell ausfuehren" - das Skript holt sich die
# Adminrechte selbst (UAC-Abfrage bestaetigen).

# ---- Selbst-Elevation: ohne Adminrechte neu mit UAC starten ----
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Fordere Adminrechte an (UAC-Abfrage bestaetigen)..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$($MyInvocation.MyCommand.Path)`"")
    exit
}

$ErrorActionPreference = "Stop"
try {
    $repo = Split-Path -Parent $PSScriptRoot
    $user = "$env:USERDOMAIN\$env:USERNAME"
    $python = Join-Path $repo ".venv\Scripts\python.exe"
    $pythonw = Join-Path $repo ".venv\Scripts\pythonw.exe"

    Write-Host ""
    Write-Host "=== 3,5-Zoll Hardware-Monitoring: Einrichtung ===" -ForegroundColor Cyan
    Write-Host "Projektordner: $repo"
    Write-Host ""

    # ---- Vorpruefungen mit klaren Meldungen ----
    if (-not (Test-Path $pythonw)) {
        throw ("Die Python-Umgebung (.venv) fehlt. Bitte zuerst im Projektordner ausfuehren:`n" +
               "    python -m venv .venv`n" +
               "    .venv\Scripts\pip install -r requirements.txt")
    }
    & $python -c "import yaml, PIL, serial" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw ("Die Python-Bibliotheken sind nicht (vollstaendig) installiert.`n" +
               "Bitte im Projektordner ausfuehren:`n" +
               "    .venv\Scripts\pip install -r requirements.txt`n" +
               "und auf Fehlermeldungen achten (Python 3.10-3.14 verwenden).")
    }
    if (-not (Test-Path (Join-Path $repo "config.yaml"))) {
        Copy-Item (Join-Path $repo "config.example.yaml") (Join-Path $repo "config.yaml")
        Write-Host "OK: config.yaml aus Vorlage erstellt." -ForegroundColor Green
    }

    # ---- Aufgabe 1: Monitor-Autostart bei Anmeldung ----
    $action = New-ScheduledTaskAction -Execute $pythonw -Argument "main.py" -WorkingDirectory $repo
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
    $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit ([TimeSpan]::Zero)
    Register-ScheduledTask -TaskName "TuringSmartScreen" -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "OK: Aufgabe 'TuringSmartScreen' registriert (Monitor-Start bei Anmeldung)." -ForegroundColor Green

    # ---- Aufgabe 2: Display-Aus bei Abmeldung/Herunterfahren ----
    $ps1 = Join-Path $repo "display-off.ps1"
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Schaltet das Turing-Display bei Abmeldung oder Herunterfahren aus (sudoAndro)</Description>
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
      <Command>C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe</Command>
      <Arguments>-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$ps1"</Arguments>
      <WorkingDirectory>$repo</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
    $xmlPath = Join-Path $env:TEMP "TuringDisplayOff.xml"
    $xml | Out-File -FilePath $xmlPath -Encoding Unicode
    schtasks /create /f /tn "TuringDisplayOff" /xml $xmlPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Aufgabe 'TuringDisplayOff' konnte nicht registriert werden." }
    Remove-Item $xmlPath -ErrorAction SilentlyContinue
    Write-Host "OK: Aufgabe 'TuringDisplayOff' registriert (Display-Aus bei Abmeldung/Shutdown)." -ForegroundColor Green

    # ---- PawnIO-Hinweis (fuer CPU-Temperatur) ----
    $pawnio = Join-Path $repo "external\PawnIO\PawnIO_setup.exe"
    if (-not (Test-Path "$env:ProgramFiles\PawnIO")) {
        Write-Host ""
        Write-Host "HINWEIS: Fuer die CPU-Temperatur wird der PawnIO-Treiber empfohlen:" -ForegroundColor Yellow
        Write-Host "  $pawnio  ->  Installieren" -ForegroundColor Yellow
    }

    Start-ScheduledTask -TaskName "TuringSmartScreen"
    Write-Host ""
    Write-Host "Fertig! Der Monitor laeuft jetzt und startet ab sofort automatisch." -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "FEHLER: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""
Read-Host "Enter druecken zum Schliessen"

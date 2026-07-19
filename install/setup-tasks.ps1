# SPDX-License-Identifier: GPL-3.0-or-later
# setup-tasks.ps1: Richtet die beiden geplanten Aufgaben ein (als Administrator ausfuehren!):
#   TuringSmartScreen - startet den Display-Monitor bei jeder Anmeldung (mit Adminrechten,
#                       noetig fuer die CPU-Temperatur via LibreHardwareMonitor)
#   TuringDisplayOff  - schaltet das Display bei Abmeldung/Herunterfahren aus
#                       (laeuft als SYSTEM, reagiert auf Windows-Ereignisse 7002/1074)
#
# Aufruf:  Rechtsklick > Mit PowerShell ausfuehren  (UAC bestaetigen)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$user = "$env:USERDOMAIN\$env:USERNAME"
$pythonw = Join-Path $repo ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $pythonw)) {
    Write-Host "FEHLER: venv nicht gefunden. Bitte zuerst installieren (siehe README):" -ForegroundColor Red
    Write-Host "  python -m venv .venv"
    Write-Host "  .venv\Scripts\pip install -r requirements.txt"
    pause; exit 1
}

if (-not (Test-Path (Join-Path $repo "config.yaml"))) {
    Copy-Item (Join-Path $repo "config.example.yaml") (Join-Path $repo "config.yaml")
}

# ---- Aufgabe 1: Monitor-Autostart bei Anmeldung ----
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "main.py" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "TuringSmartScreen" -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null
Write-Host "OK: Aufgabe 'TuringSmartScreen' registriert (Start bei Anmeldung)." -ForegroundColor Green

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
Remove-Item $xmlPath -ErrorAction SilentlyContinue
Write-Host "OK: Aufgabe 'TuringDisplayOff' registriert (Display-Aus bei Abmeldung/Shutdown)." -ForegroundColor Green

Start-ScheduledTask -TaskName "TuringSmartScreen"
Write-Host ""
Write-Host "Fertig! Der Monitor laeuft jetzt und startet ab sofort automatisch." -ForegroundColor Cyan
pause

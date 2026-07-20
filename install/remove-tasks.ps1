# SPDX-License-Identifier: GPL-3.0-or-later
# remove-tasks.ps1: Entfernt die geplanten Aufgaben wieder.
# Aufruf: Rechtsklick > "Mit PowerShell ausfuehren" (holt sich Adminrechte selbst)

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell -Verb RunAs -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$($MyInvocation.MyCommand.Path)`"")
    exit
}

schtasks /end /tn "TuringSmartScreen" 2>$null | Out-Null
schtasks /delete /f /tn "TuringSmartScreen" 2>$null
schtasks /delete /f /tn "TuringDisplayOff" 2>$null
Write-Host "Aufgaben entfernt. Das Display wird nicht mehr automatisch gestartet." -ForegroundColor Yellow
Read-Host "Enter druecken zum Schliessen"

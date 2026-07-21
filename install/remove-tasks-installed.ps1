# SPDX-License-Identifier: GPL-3.0-or-later
# remove-tasks-installed.ps1: Wird vom Deinstallationsprogramm aufgerufen (bereits mit
# Adminrechten). Beendet und entfernt die beiden geplanten Aufgaben.
schtasks /end /tn "TuringSmartScreen" 2>$null | Out-Null
schtasks /delete /f /tn "TuringSmartScreen" 2>$null | Out-Null
schtasks /delete /f /tn "TuringDisplayOff" 2>$null | Out-Null

# Laufende Monitor-/Display-Prozesse beenden, damit die Dateien geloescht werden koennen
Get-Process -Name "sudoAndro-Monitor", "sudoAndro-Studio", "display-off" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

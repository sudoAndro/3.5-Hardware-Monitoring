# SPDX-License-Identifier: GPL-3.0-or-later
# remove-tasks.ps1: Entfernt die geplanten Aufgaben wieder (als Administrator ausfuehren)

schtasks /end /tn "TuringSmartScreen" 2>$null | Out-Null
schtasks /delete /f /tn "TuringSmartScreen" 2>$null
schtasks /delete /f /tn "TuringDisplayOff" 2>$null
Write-Host "Aufgaben entfernt. Das Display wird nicht mehr automatisch gestartet." -ForegroundColor Yellow
pause

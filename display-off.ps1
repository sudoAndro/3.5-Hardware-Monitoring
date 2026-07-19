# SPDX-License-Identifier: GPL-3.0-or-later
# display-off.ps1: Wrapper fuer display-off.exe (pyserial-basiert).
# Die Aufgabe "TuringDisplayOff" (SYSTEM) ruft dieses Skript bei Abmeldung/Herunterfahren auf.
# Die eigentliche Arbeit macht display-off.exe - der .NET-SerialPort-Weg erreichte das
# CH340-Display nicht (Monitor nutzt pyserial, die Exe nutzt exakt denselben Stack).

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $repo "display-off.exe"
$logFile = Join-Path $repo "display-off.log"

if (Test-Path $exe) {
    $p = Start-Process -FilePath $exe -Wait -PassThru -WindowStyle Hidden
    exit $p.ExitCode
} else {
    Add-Content -Path $logFile -Value ("{0:dd.MM.yyyy HH:mm:ss} FEHLER - display-off.exe nicht gefunden" -f (Get-Date))
    exit 1
}

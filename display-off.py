# SPDX-License-Identifier: GPL-3.0-or-later
# display-off.py: Schaltet das Turing-Display (Rev. A) direkt ueber den COM-Port aus.
# Wird als display-off.exe (PyInstaller) von der Aufgabe "TuringDisplayOff" bei
# Abmeldung/Herunterfahren ausgefuehrt. Nutzt bewusst denselben Stack wie der Monitor
# (pyserial, identische Port-Parameter) - der .NET-SerialPort-Weg erreichte das Display nicht.
#
# Ablauf:
# 1. Warten, bis der (hart gekillte) Monitor-Prozess den COM-Port freigegeben hat
# 2. Null-Padding (Vielfaches von 6 Bytes, groesser als ein Vollbild) - schliesst
#    eine angefangene Bilduebertragung ab
# 3. SCREEN_OFF (108) in allen 6 moeglichen Byte-Versaetzen - das Protokoll hat kein
#    Framing; nach einem Kill mitten im Befehl zaehlt der Controller versetzt weiter

import datetime
import os
import re
import sys
import time

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_PATH = os.path.join(BASE_DIR, "display-off.log")
SCREEN_OFF = 108


def log(msg):
    try:
        with open(LOG_PATH, "at", encoding="utf8") as f:
            f.write("%s %s\n" % (datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), msg))
    except Exception:
        pass


def main():
    import serial

    com_port = "COM3"
    try:
        with open(os.path.join(BASE_DIR, "config.yaml"), "rt", encoding="utf8") as f:
            m = re.search(r'^\s*COM_PORT:\s*"?(COM\d+)"?', f.read(), re.MULTILINE)
            if m:
                com_port = m.group(1)
    except Exception:
        pass

    packet = bytes([0, 0, 0, 0, 0, SCREEN_OFF])
    # Klone (z. B. Temu "UsbPCMonitor") ignorieren SCREEN_OFF. Fuer sie:
    # TO_BLACK (103) macht den Bildinhalt schwarz, SET_BRIGHTNESS (110, x=255)
    # dimmt das Backlight auf Minimum - zusammen wirkt das Display komplett aus.
    packet_black = bytes([0, 0, 0, 0, 0, 103])
    packet_dark = bytes([63, 192, 0, 0, 0, 110])
    padding = bytes(310806)  # 6 x 51801, mehr als ein Vollbild (320x480x2)

    last_error = None
    for attempt in range(30):  # bis zu ~15 s auf freien Port warten
        try:
            # Exakt dieselben Parameter wie library/lcd/lcd_comm.py openSerial()
            s = serial.Serial(com_port, 115200, timeout=1, rtscts=True)
            s.write(padding)
            for _ in range(6):
                s.write(packet)
                s.write(bytes([0]))  # Versatz um ein Byte weiterschieben
            for _ in range(6):
                s.write(packet_black)
                s.write(bytes([0]))
            for _ in range(6):
                s.write(packet_dark)
                s.write(bytes([0]))
            s.flush()
            time.sleep(0.3)
            s.close()
            log("OK - Padding + SCREEN_OFF-Sweep an %s gesendet (pyserial, Versuch %d)"
                % (com_port, attempt + 1))
            return 0
        except Exception as e:
            last_error = e
            time.sleep(0.5)
    log("FEHLER - Port %s nicht erreichbar: %s" % (com_port, last_error))
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log("FEHLER - %r" % e)
        sys.exit(1)

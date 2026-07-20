@echo off
rem Oeffnet die klassische Konfigurations-Oberflaeche des Basisprojekts (configure.py)
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo FEHLER: Die Python-Umgebung fehlt. Bitte zuerst installieren:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import yaml, PIL, serial" >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Die Python-Bibliotheken sind nicht installiert. Bitte ausfuehren:
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist config.yaml copy config.example.yaml config.yaml >nul
start "" ".venv\Scripts\pythonw.exe" configure.py

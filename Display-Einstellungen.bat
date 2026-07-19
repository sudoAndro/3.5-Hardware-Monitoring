@echo off
rem Oeffnet die klassische Konfigurations-Oberflaeche des Basisprojekts (configure.py)
cd /d "%~dp0"
if not exist config.yaml copy config.example.yaml config.yaml >nul
start "" ".venv\Scripts\pythonw.exe" configure.py

@echo off
rem sudoAndro Studio: Steuerzentrale + Drag&Drop-Editor fuer das Display
cd /d "%~dp0"
if not exist config.yaml copy config.example.yaml config.yaml >nul
start "" ".venv\Scripts\pythonw.exe" theme-studio.py

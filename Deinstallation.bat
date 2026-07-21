@echo off
rem Entfernt die geplanten Aufgaben wieder (Monitor-Autostart + Display-Aus)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install\remove-tasks.ps1"

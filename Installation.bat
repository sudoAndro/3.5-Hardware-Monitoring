@echo off
rem =====================================================================
rem  3,5-Zoll Hardware-Monitoring - Einrichtung (sudoAndro)
rem  Doppelklicken genuegt: richtet Autostart + Display-Aus-Aufgaben ein.
rem  (Startet das PowerShell-Skript an der ExecutionPolicy vorbei und
rem   holt sich die Adminrechte automatisch per UAC-Abfrage.)
rem =====================================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install\setup-tasks.ps1"

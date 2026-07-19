@echo off
rem Oeffnet den Theme-Editor mit Live-Vorschau fuer ein bestimmtes Theme
cd /d "%~dp0"
set THEME=3.5inchTheme2
set /p THEME="Welches Theme bearbeiten? (Enter fuer %THEME%): "
".venv\Scripts\python.exe" theme-editor.py "%THEME%"
pause

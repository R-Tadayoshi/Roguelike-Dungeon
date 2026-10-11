@echo off
rem Double-click to play. Needs Python 3.11+ installed (python.org).
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py roguelike.pyz %*) else (python roguelike.pyz %*)
if errorlevel 1 pause

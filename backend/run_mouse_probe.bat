@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -B mouse_input_probe.py
) else (
    python -B mouse_input_probe.py
)
if errorlevel 1 pause

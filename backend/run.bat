@echo off
cd /d "%~dp0"
echo Starting Client-Project...
echo Open http://127.0.0.1:8765 in your browser if it does not open automatically.
echo Keep this window open while testing. Press Ctrl+C to stop.
echo.
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -B -u app.py
) else (
    python -B -u app.py
)
if errorlevel 1 (
    echo.
    echo Program stopped with an error. Please copy the message above.
    pause
)
 

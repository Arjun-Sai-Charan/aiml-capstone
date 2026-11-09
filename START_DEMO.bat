@echo off
setlocal
title Fraud Detection Demo - Start
echo Starting the fraud detection demo in Ubuntu on WSL2...
echo The first start may take a while while Docker builds the application images.
wsl.exe -d Ubuntu -- bash -lc "cd ~/fraud-platform && ./scripts/demo_start.sh"
if errorlevel 1 goto failed
echo.
echo The demo is ready. Opening the dashboard in your browser.
start "" "http://localhost:8501"
echo Keep Docker Desktop running while you use the demo.
pause
exit /b 0

:failed
echo.
echo The demo did not start. This window will stay open so you can read the error.
echo Send the newest demo_logs/start-*.log file for help.
pause
exit /b 1

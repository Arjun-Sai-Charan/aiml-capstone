@echo off
setlocal
cd /d "%TEMP%" >nul 2>&1
title Fraud Detection Demo - Stop
echo Stopping the demo containers. Images and data will be kept.
wsl.exe -d Ubuntu -- bash -lc "cd ~/fraud-platform && ./scripts/demo_stop.sh"
if errorlevel 1 goto failed
echo.
echo Demo stopped. You can start it again by double-clicking START_DEMO.bat.
pause
exit /b 0

:failed
echo.
echo The demo could not be stopped. Keep this window open and send the error text.
pause
exit /b 1

@echo off
setlocal
title Fraud Detection Demo - Check
echo Checking Docker, demo containers, API, scored transactions, alerts, and dashboard...
wsl.exe -d Ubuntu -- bash -lc "cd ~/fraud-platform && ./scripts/demo_check.sh"
if errorlevel 1 goto failed
echo.
echo All demo checks passed.
pause
exit /b 0

:failed
echo.
echo One or more checks failed. Keep this window open and send the newest demo_logs/check-*.log file.
pause
exit /b 1

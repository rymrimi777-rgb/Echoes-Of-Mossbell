@echo off
title Echoes of Mossbell - Phone Web Server
cls
echo ================================================================
echo          Echoes of Mossbell - Web Mobile Server
echo ================================================================
echo.
echo   1. Make sure your phone is connected to the SAME Wi-Fi.
echo.
echo   2. Open Chrome or Safari on your phone and go to:
echo.
echo      http://192.168.147.61:8000
echo.
echo ================================================================
echo  Press Ctrl+C in this window when you want to stop the server.
echo ================================================================
echo.
python -m http.server 8000 --directory build\web --bind 0.0.0.0
pause

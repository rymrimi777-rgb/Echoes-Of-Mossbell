@echo off
title Push Echoes of Mossbell to GitHub
echo ========================================================
echo   Pushing Echoes of Mossbell to GitHub
echo   Repository: https://github.com/rymrimi777-rgb/Echoes-Of-Mossbell
echo ========================================================
echo.
echo If GitHub asks you to sign in, click "Sign in with your browser".
echo.
git push -u origin main
echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo   [SUCCESS] Code pushed to GitHub!
    echo   GitHub Actions is now automatically building your APK!
    echo   Check: https://github.com/rymrimi777-rgb/Echoes-Of-Mossbell/actions
    echo ========================================================
) else (
    echo.
    echo [!] If you haven't authenticated yet, run:
    echo     git push -u origin main
    echo in terminal or generate a GitHub Personal Access Token.
)
echo.
pause

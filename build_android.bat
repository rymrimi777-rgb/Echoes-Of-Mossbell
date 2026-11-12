@echo off
echo =========================================================
echo   Echoes of Mossbell - Android APK Build Helper
echo =========================================================
echo.
echo Python/Pygame Android builds (via python-for-android/Buildozer)
echo require a Linux environment with NDK cross-compilers.
echo.

where wsl >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] WSL is available on this system.
    echo Running buildozer inside WSL...
    wsl bash -c "buildozer android debug"
    goto end
)

where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Docker is available on this system.
    echo Building APK using official kivy/buildozer container...
    docker run --rm -v "%cd%":/home/user/hostcwd kivy/buildozer android debug
    goto end
)

echo [!] NOTICE:
echo Buildozer and python-for-android require a POSIX environment
echo (WSL2, Docker, or Linux) to cross-compile CPython and SDL2 for Android.
echo.
echo How to build the APK:
echo 1. Option A (WSL): Run 'wsl --install' in PowerShell, then inside Ubuntu run:
echo      pip install buildozer
echo      buildozer android debug
echo.
echo 2. Option B (Docker):
echo      docker run --rm -v "%%cd%%":/home/user/hostcwd kivy/buildozer android debug
echo.
echo 3. Option C (GitHub Actions):
echo      Push to GitHub and the automated workflow will build the APK in the cloud!
echo.
:end
pause


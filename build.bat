@echo off
echo ============================================
echo   Building Echoes of Mossbell - Windows EXE
echo ============================================
echo.

python3 -m PyInstaller --noconfirm --onedir --windowed ^
    --name "EchoesOfMossbell" ^
    --add-data "assets;assets" ^
    --add-data "saves;saves" ^
    --add-data "Ocean_Nostalgia_Pygame_Ready;Ocean_Nostalgia_Pygame_Ready" ^
    --icon NUL ^
    game\main.py

echo.
echo Build complete! Check the dist\EchoesOfMossbell folder.
pause


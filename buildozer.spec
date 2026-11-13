[app]

# (str) Title of your application
title = Echoes of Mossbell

# (str) Package name (lowercase alphanumeric)
package.name = echoesofmossbell

# (str) Package domain (needed for android/ios packaging)
package.domain = org.mossbellgames

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (empty = include all matching extensions)
source.include_exts = py,png,jpg,jpeg,ttf,otf,json,mp3,wav,ogg,txt

# (list) List of directories to include
source.include_patterns = assets/*,game/*,Ocean_Nostalgia_Pygame_Ready/characters/*

# (list) List of directories to exclude from the APK
source.exclude_dirs = build, dist, _web_staging, temp_pages, saves, .git, .gemini, .venv, Free_Chiptune_Asset_Pack, RPG_fantasy_tilesets, Handheld-4-Shade-Starter-FREE, GameBoy_Touch_Controls_Split, scripts, node_modules

# (list) List of file patterns to exclude
source.exclude_patterns = *.spec, *.bat, *.zip, *.md, *.txt, err.txt, screenshot_*.png, *.aseprite, default.tmpl, pygbag.ini

# (str) Application versioning
version = 1.1.0

# (list) Application requirements
# pygame-ce runs on python-for-android via sdl2 bootstrap
requirements = python3,pygame-ce

# (str) Supported orientation (landscape, sensorLandscape, portrait, sensorPortrait or all)
orientation = all

# (bool) Indicate if the application should be fullscreen
fullscreen = 1

# (str) Icon of the application
icon.filename = assets/android/icon.png

# (str) Presplash of the application
presplash.filename = assets/android/presplash.png

# (list) Permissions
android.permissions = WAKE_LOCK

# (int) Target Android API
android.api = 34

# (int) Minimum API your APP will support (Android 5.0+)
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, skip trying to update the Android SDK
android.skip_update = False

# (bool) Automatically accept SDK licenses
android.accept_sdk_license = True

# (str) Bootstrap to use for android (sdl2 is required for pygame-ce)
p4a.bootstrap = sdl2

# (list) Android architectures to build for (arm64-v8a covers 95%+ of active Android devices)
android.archs = arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

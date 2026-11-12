[app]

# (str) Title of your application
title = Echoes of Mossbell

# (str) Package name
package.name = echoesofmossbell

# (str) Package domain (needed for android/ios packaging)
package.domain = org.mossbellgames

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,ttf,otf,json,mp3,wav,ogg,txt

# (list) List of directory to include
source.include_patterns = assets/*,game/*,Ocean_Nostalgia_Pygame_Ready/*

# (list) List of exclusions using pattern matching
source.exclude_patterns = build/*,dist/*,.git/*,.gemini/*,*.spec,*.bat

# (str) Application versioning
version = 1.1.0

# (list) Application requirements
# pygame-ce runs on python-for-android via sdl2 bootstrap
requirements = python3,pygame-ce

# (str) Supported orientation (one of landscape, sensorLandscape, portrait, sensorPortrait or all)
orientation = all

# (bool) Indicate if the application should be fullscreen to not
fullscreen = 1

# (list) Permissions
android.permissions = WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APP will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) Bootstrap to use for android
p4a.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1


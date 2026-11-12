# Echoes of Mossbell

A retro RPG game inspired by classic 1990s Game Boy handheld titles.
Built with Python and Pygame-CE. Fully offline, standalone, and cross-platform (Windows & Android mobile ready).

---

## Story

People have been vanishing from the quiet village of Mossbell.
As a young hero, you must explore the Whispering Woods, uncover ancient ruins and crypts, and face the shadow that lurks in the depths to break the eternal curse.

---

## Universal Controls (Windows Desktop & Mobile)

The game features dual input handling: keyboard and touchscreen inputs are unified and work simultaneously.

### Keyboard Controls (QWERTY + AZERTY + Arrows)
| Key | Action |
| :--- | :--- |
| **Arrow Keys / W A S D / Z Q S D** | 4-directional fluid movement |
| **Space / Enter / E / Z** | Interact, talk to NPCs, check signs, open chests, advance dialogue |
| **Shift / X** | Hold to sprint / dash |
| **I / B** | Toggle Categorized Inventory |
| **Escape / P / Tab** | Pause Menu / Settings |
| **X / Escape / Backspace** | Cancel / Back |

### Mobile Touch Controls (Game Boy-Style Pixel Art)
- **Virtual 4-Way D-Pad** (Lower-left): Authentic 3-frame animated directional pad (idle, mid, pressed) with smooth thumb-sliding support.
- **Button A** (Lower-right): Primary action (Talk, Interact, Confirm, Advance dialogue).
- **Button B** (Lower-right): Secondary action (Hold to sprint/dash, Cancel, Close menus).
- **Start Button** (Bottom-center / Lower console): Pause menu and settings toggle.
- **Select Button** (Bottom-center / Lower console): Instant categorized inventory toggle.
- **Expanded Touch Targets**: Invisible padding around buttons ensures comfortable, accurate thumb touches without missing buttons.
- **Visual Press Animations**: Real-time 3-frame tactile feedback (`idle.png` -> `mid.png` -> `pressed.png`).
- **Simultaneous Multi-Touch**: Hold D-pad direction for continuous walking while tapping A to interact or B to sprint.
- **Adaptive Layout**:
  - **Landscape Mode**: Thumb controls in lower corners and bottom bar.
  - **Portrait Mode**: Authentic Game Boy handheld layout (screen on top half, console D-pad & buttons on bottom half).
- **Asset Attribution**: Buttons designed by Luna Desuwa (GBStudio Keyboard Buttons: https://okutasan.itch.io).

---

## Audio System

Centralized audio management (`game.audio.AudioManager`) supporting WAV, OGG, and MP3 formats with debounce protection:

```
assets/audio/
├── music/        # Distinct background music for all 8 maps + title screen
├── player/       # footsteps (grass/stone), sprint dash, hurt, heal
├── npc/          # typewriter voice blips (blip/low/high), greeting, quest start/done
├── environment/  # door open/close, water splash, secret discovery, dungeon echoes
├── combat/       # sword swing, hit impact, shield block, boss roar
├── ui/           # menu move, menu select, menu cancel, pause chime
└── items/        # item pickup, consumable use, chest open, key turn, coin pickup
```

### In-Game Audio & Control Settings
Open the Pause Menu (`Escape` / `P` / `MENU` button) -> **SETTINGS**:
- **Music Volume**: Adjust from `0%` to `100%` (using `<-` / `->`).
- **SFX Volume**: Adjust from `0%` to `100%`.
- **Mute / Unmute**: Toggle all audio on or off with a single tap.
- **Touch Controls**: Toggle between `AUTO`, `ALWAYS`, and `HIDDEN`.
- **Touch Size (T.Size)**: Adjust virtual button size (`NORMAL`, `LARGE`, `SMALL`).
- **Touch Opacity (Alpha)**: Adjust button transparency (`100%`, `75%`, `50%`).

---

## World Maps & Music

1. **Mossbell Village**: Main village with pond and flower garden (`bpag02 - Game Theme.mp3`)
2. **Player Cottage**: Cozy thatched house with resting bed (`cag01 - Title Screen.mp3`)
3. **Elder Orin's Archive**: Village history repository (`cag02 - Game Theme-A.mp3`)
4. **Whispering Woods**: Ancient forest (`cag04 - Game Theme-B.mp3`)
5. **Deep Whispering Woods**: Dense enchanted forest (`cag07 - Game Theme-A+B.mp3`)
6. **Watchtower Ruins**: Fallen fortress (`stg02 - Game Start.mp3`)
7. **Forgotten Crypt**: Underground dungeon (`bpag03 - Game Over.mp3`)
8. **Shadow Grotto**: King Aldous's cavern (`stg05 - Game Over.mp3`)

---

## Running and Building

### Windows Standalone Executable
- The compiled standalone executable is ready in `dist/EchoesOfMossbell/EchoesOfMossbell.exe`.
- Or double-click `PLAY_GAME.bat`.
- To rebuild: run `build.bat`.

### Running from Python Source
```bash
python -m pip install -r requirements.txt
python main.py
```

### Android APK Build
The project is configured for Android packaging via `buildozer.spec` and `python-for-android` (P4A SDL2 bootstrap):
1. **GitHub Actions (Recommended / Zero-Setup)**:
   - Push repository to GitHub; the included workflow `.github/workflows/android.yml` automatically builds the Android APK in the cloud and provides the download artifact.
2. **Local WSL / Linux**:
   ```bash
   pip install buildozer
   buildozer android debug
   ```
3. **Local Docker**:
   ```bash
   docker run --rm -v "%cd%":/home/user/hostcwd kivy/buildozer android debug
   ```
*(Note: Android cross-compilation of CPython/SDL2 native binaries requires a Linux host; native Windows builds are routed through WSL or Docker).*

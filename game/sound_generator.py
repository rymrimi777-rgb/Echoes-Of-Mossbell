"""
Authentic Retro 8-bit Chiptune Sound Generator.
Synthesizes classic Game Boy / NES style sound effects using Python standard library (wave, math, struct).
Creates clean, offline WAV audio assets for player, npc, environment, combat, ui, and items.
"""
import os
import math
import struct
import random
import wave


def generate_wave_file(filename, samples, sample_rate=22050):
    """Write float samples (-1.0 to 1.0) into a 16-bit mono WAV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        int_samples = []
        for s in samples:
            val = max(-1.0, min(1.0, s))
            int_samples.append(int(val * 32767))
        raw_data = struct.pack(f"<{len(int_samples)}h", *int_samples)
        wav.writeframes(raw_data)


def square_wave(freq, duration_s, duty=0.5, slide=0.0, volume=0.7, sample_rate=22050):
    """Square wave with optional frequency slide and exponential decay envelope."""
    total_samples = int(duration_s * sample_rate)
    samples = []
    current_freq = freq
    phase = 0.0

    for i in range(total_samples):
        t = i / total_samples
        # Exponential volume envelope
        env = (1.0 - t) ** 1.5 * volume
        # Frequency slide
        current_freq += slide / sample_rate
        if current_freq <= 10.0:
            current_freq = 10.0

        phase += 2.0 * math.pi * current_freq / sample_rate
        # Square duty cycle
        cycle = (phase / (2.0 * math.pi)) % 1.0
        val = 1.0 if cycle < duty else -1.0
        samples.append(val * env)

    return samples


def triangle_wave(freq, duration_s, volume=0.8, sample_rate=22050):
    """Smooth triangle wave with gentle envelope."""
    total_samples = int(duration_s * sample_rate)
    samples = []
    phase = 0.0

    for i in range(total_samples):
        t = i / total_samples
        env = math.sin(t * math.pi) * volume if t < 0.2 else (1.0 - t) * volume
        phase += 2.0 * math.pi * freq / sample_rate
        cycle = (phase / (2.0 * math.pi)) % 1.0
        # Triangle from -1 to 1
        val = 4.0 * abs(cycle - 0.5) - 1.0
        samples.append(val * env)

    return samples


def noise_wave(duration_s, volume=0.6, decay=2.0, filter_val=0.5, sample_rate=22050):
    """Filtered noise burst with decay envelope."""
    total_samples = int(duration_s * sample_rate)
    samples = []
    last_val = 0.0

    for i in range(total_samples):
        t = i / total_samples
        env = math.exp(-t * decay) * volume
        raw = random.uniform(-1.0, 1.0)
        # Simple one-pole lowpass filter
        filtered = last_val + filter_val * (raw - last_val)
        last_val = filtered
        samples.append(filtered * env)

    return samples


def arpeggio(freqs, step_duration_s, duty=0.5, volume=0.7, sample_rate=22050):
    """Rapid sequence of square notes (classic chiptune jingle/powerup)."""
    samples = []
    for f in freqs:
        samples.extend(square_wave(f, step_duration_s, duty=duty, volume=volume, sample_rate=sample_rate))
    return samples


def build_all_audio(base_audio_dir):
    """Generates all categorized sound effects into assets/audio/<category>/"""
    print(f"Synthesizing audio assets into {base_audio_dir}...")

    # 1. PLAYER SFX
    p_dir = os.path.join(base_audio_dir, "player")
    # Footstep grass: light rustle
    generate_wave_file(os.path.join(p_dir, "step_grass.wav"),
                       noise_wave(0.06, volume=0.25, decay=8.0, filter_val=0.4))
    # Footstep stone: crisp tap
    step_stone = square_wave(180, 0.04, duty=0.25, slide=-1200, volume=0.25)
    generate_wave_file(os.path.join(p_dir, "step_stone.wav"), step_stone)
    # Dash / run: quick whoosh
    dash = noise_wave(0.12, volume=0.4, decay=5.0, filter_val=0.6)
    generate_wave_file(os.path.join(p_dir, "dash.wav"), dash)
    # Hurt / damage: sharp descending crunch
    hurt = square_wave(220, 0.18, duty=0.5, slide=-1800, volume=0.6)
    generate_wave_file(os.path.join(p_dir, "hurt.wav"), hurt)
    # Heal: ascending melodic chime
    heal = arpeggio([330, 440, 554, 659, 880], 0.07, duty=0.5, volume=0.5)
    generate_wave_file(os.path.join(p_dir, "heal.wav"), heal)

    # 2. NPC SFX
    npc_dir = os.path.join(base_audio_dir, "npc")
    # Dialogue typewriter blips (high, mid, low)
    generate_wave_file(os.path.join(npc_dir, "talk_blip.wav"),
                       square_wave(440, 0.035, duty=0.25, slide=200, volume=0.35))
    generate_wave_file(os.path.join(npc_dir, "talk_low.wav"),
                       square_wave(280, 0.04, duty=0.5, slide=100, volume=0.35))
    generate_wave_file(os.path.join(npc_dir, "talk_high.wav"),
                       square_wave(600, 0.03, duty=0.125, slide=300, volume=0.3))
    # Greeting / attention
    greet = arpeggio([440, 659], 0.06, duty=0.5, volume=0.4)
    generate_wave_file(os.path.join(npc_dir, "greeting.wav"), greet)
    # Quest start fanfare
    q_start = arpeggio([262, 330, 392, 523], 0.08, duty=0.5, volume=0.5)
    generate_wave_file(os.path.join(npc_dir, "quest_start.wav"), q_start)
    # Quest done fanfare
    q_done = arpeggio([392, 523, 659, 784, 1046], 0.09, duty=0.5, volume=0.6)
    generate_wave_file(os.path.join(npc_dir, "quest_done.wav"), q_done)

    # 3. ENVIRONMENT SFX
    env_dir = os.path.join(base_audio_dir, "environment")
    # Door open: wooden sliding squeak
    door_open = square_wave(160, 0.15, duty=0.25, slide=400, volume=0.4)
    generate_wave_file(os.path.join(env_dir, "door_open.wav"), door_open)
    # Door close: solid thud
    door_close = noise_wave(0.12, volume=0.5, decay=6.0, filter_val=0.25)
    generate_wave_file(os.path.join(env_dir, "door_close.wav"), door_close)
    # Water splash: soft watery ripple
    water = noise_wave(0.18, volume=0.35, decay=4.0, filter_val=0.7)
    generate_wave_file(os.path.join(env_dir, "water_splash.wav"), water)
    # Secret discovered: classic Zelda-like chime
    secret = arpeggio([784, 740, 622, 440, 415, 659, 830, 1046], 0.07, duty=0.5, volume=0.5)
    generate_wave_file(os.path.join(env_dir, "secret.wav"), secret)
    # Dungeon echo: eerie resonant sweep
    dungeon = triangle_wave(110, 0.4, volume=0.5)
    generate_wave_file(os.path.join(env_dir, "dungeon_echo.wav"), dungeon)

    # 4. COMBAT SFX
    c_dir = os.path.join(base_audio_dir, "combat")
    # Sword swing: quick slicing noise
    swing = noise_wave(0.1, volume=0.45, decay=8.0, filter_val=0.8)
    generate_wave_file(os.path.join(c_dir, "sword_swing.wav"), swing)
    # Hit enemy: punchy collision
    hit = square_wave(300, 0.12, duty=0.5, slide=-1600, volume=0.6)
    generate_wave_file(os.path.join(c_dir, "hit_enemy.wav"), hit)
    # Shield block: metallic deflection
    block = square_wave(880, 0.1, duty=0.125, slide=-4000, volume=0.5)
    generate_wave_file(os.path.join(c_dir, "shield_block.wav"), block)
    # Boss roar: low rumbling tremor
    boss = square_wave(90, 0.45, duty=0.5, slide=-200, volume=0.7)
    generate_wave_file(os.path.join(c_dir, "boss_roar.wav"), boss)

    # 5. UI SFX
    ui_dir = os.path.join(base_audio_dir, "ui")
    # Menu move: subtle click
    generate_wave_file(os.path.join(ui_dir, "menu_move.wav"),
                       square_wave(520, 0.03, duty=0.25, slide=-300, volume=0.3))
    # Menu select: bright confirm beep
    generate_wave_file(os.path.join(ui_dir, "menu_select.wav"),
                       square_wave(660, 0.06, duty=0.5, slide=400, volume=0.4))
    # Menu cancel: descending back blip
    generate_wave_file(os.path.join(ui_dir, "menu_cancel.wav"),
                       square_wave(440, 0.06, duty=0.25, slide=-800, volume=0.35))
    # Pause sound: dual chime
    generate_wave_file(os.path.join(ui_dir, "pause.wav"),
                       arpeggio([523, 659], 0.05, duty=0.5, volume=0.45))

    # 6. ITEMS SFX
    it_dir = os.path.join(base_audio_dir, "items")
    # Item pickup: bright ascending sparkle
    pickup = arpeggio([587, 880, 1174], 0.05, duty=0.5, volume=0.45)
    generate_wave_file(os.path.join(it_dir, "item_pickup.wav"), pickup)
    # Item use / drink potion: bubbling chime
    potion = arpeggio([392, 493, 587, 784], 0.06, duty=0.25, volume=0.45)
    generate_wave_file(os.path.join(it_dir, "item_use.wav"), potion)
    # Chest open: dramatic latch opening
    chest = arpeggio([262, 330, 392, 523, 659], 0.06, duty=0.5, volume=0.55)
    generate_wave_file(os.path.join(it_dir, "chest_open.wav"), chest)
    # Key turn: metallic ratchet
    key_turn = square_wave(750, 0.08, duty=0.125, slide=1000, volume=0.4)
    generate_wave_file(os.path.join(it_dir, "key_turn.wav"), key_turn)
    # Coin collect: classic high ding
    coin = arpeggio([987, 1318], 0.07, duty=0.5, volume=0.4)
    generate_wave_file(os.path.join(it_dir, "coin.wav"), coin)

    print("All categorized sound effects generated successfully!")


if __name__ == "__main__":
    import sys
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio")
    build_all_audio(dest)


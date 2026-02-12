#!/usr/bin/env python3
"""Generate lamp program responses for remaining prompts in chunk 2."""

import json
import random
import hashlib

random.seed(42)

def prompt_hash(prompt):
    """Deterministic hash for consistent but varied output."""
    return int(hashlib.md5(prompt.encode()).hexdigest(), 16)

def pick(prompt, options):
    """Pick from options deterministically based on prompt."""
    h = prompt_hash(prompt)
    return options[h % len(options)]

def jitter(prompt, base, spread=0.15):
    """Add slight variation to a numeric value."""
    h = prompt_hash(prompt)
    factor = 1.0 + (((h % 1000) / 1000.0) - 0.5) * 2 * spread
    return int(base * factor)

def make_program(name, steps, loop=None, on_complete=None):
    prog = {"program": {"name": name, "steps": steps}}
    if loop:
        prog["program"]["loop"] = loop
    if on_complete:
        prog["program"]["on_complete"] = on_complete
    return json.dumps(prog, separators=(',', ':'))

def solid_step(sid, color, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "solid", "params": {"color": color}}, "duration": duration}

def gradient_step(sid, c1, c2, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "gradient", "params": {"color": c1, "color2": c2}}, "duration": duration}

def breathing_step(sid, color, speed, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "breathing", "params": {"color": color, "speed": speed}}, "duration": duration}

def wave_step(sid, c1, c2, speed, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "wave", "params": {"color": c1, "color2": c2, "speed": speed}}, "duration": duration}

def rainbow_step(sid, speed, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "rainbow", "params": {"speed": speed}}, "duration": duration}

def pulse_step(sid, color, speed, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "pulse", "params": {"color": color, "speed": speed}}, "duration": duration}

def sparkle_step(sid, color, bg, speed, density, duration=None):
    return {"id": sid, "command": {"type": "pattern", "name": "sparkle", "params": {"color": color, "bgColor": bg, "speed": speed, "density": density}}, "duration": duration}

def render_step(sid, elements, duration=None):
    return {"id": sid, "command": {"type": "render", "elements": elements}, "duration": duration}

# ============================================================
# TIME-OF-DAY response generators
# ============================================================

def gen_early_morning(prompt):
    """Very early morning, pre-dawn (3am-5am). Ultra dim, deep blues/purples."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Pre-Dawn Quiet", [
            breathing_step("glow", "#191970", jitter(prompt, 5000, 0.2), None)
        ])
    elif v == 1:
        return make_program("Night Whisper", [
            gradient_step("dim", "#0a0a2e", "#191970", None)
        ])
    elif v == 2:
        return make_program("Deep Night Glow", [
            breathing_step("soft", "#1a1a3a", jitter(prompt, 6000), None)
        ])
    elif v == 3:
        return make_program("Wee Hours", [
            solid_step("dim", "#0d0d2b", None)
        ])
    else:
        return make_program("Before Dawn", [
            breathing_step("pulse", "#2a1a4a", jitter(prompt, 5500), None)
        ])

def gen_dawn(prompt):
    """Dawn/sunrise (5am-7am). Gentle warm colors emerging from dark."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Gentle Dawn", [
            gradient_step("dark", "#1a1a3a", "#2a1a3a", 10000),
            gradient_step("first", "#2a1a4a", "#4a2a3a", 15000),
            gradient_step("warm", "#FF6B4A", "#FFE4C4", None)
        ])
    elif v == 1:
        return make_program("Sunrise Wake", [
            breathing_step("pre", "#483D8B", 5000, 20000),
            gradient_step("rise", "#D88B70", "#FFE4C4", None)
        ])
    elif v == 2:
        return make_program("Morning First Light", [
            solid_step("dark", "#191970", 8000),
            gradient_step("pink", "#CC6666", "#FFD0B0", 15000),
            solid_step("warm", "#FFE4C4", None)
        ])
    elif v == 3:
        return make_program("Dawn Breathing", [
            breathing_step("emerge", "#4A3060", 4500, 20000),
            breathing_step("warm", "#D88B70", 3500, None)
        ])
    elif v == 4:
        return make_program("Crack Of Dawn", [
            gradient_step("dark", "#0a0a2e", "#1a1a3a", 12000),
            gradient_step("horizon", "#663344", "#FFB088", 18000),
            gradient_step("sunrise", "#FF8855", "#FFEEDD", None)
        ])
    else:
        return make_program("Sunrise Sequence", [
            breathing_step("night", "#1a1a4a", 5000, 15000),
            wave_step("color", "#FF6B4A", "#FFD700", 3000, None)
        ])

def gen_morning(prompt):
    """Morning (7am-10am). Bright, warm, energizing."""
    h = prompt_hash(prompt)
    v = h % 7
    if v == 0:
        return make_program("Morning Energy", [
            gradient_step("main", "#FFE4C4", "#F0F8FF", None)
        ])
    elif v == 1:
        return make_program("Good Morning", [
            solid_step("bright", "#FFBF00", 5000),
            gradient_step("settle", "#FFE4C4", "#FFF8F0", None)
        ])
    elif v == 2:
        return make_program("Wake Up Light", [
            breathing_step("gentle", "#FFD0A0", 3000, 15000),
            solid_step("awake", "#FFF0E0", None)
        ])
    elif v == 3:
        return make_program("Morning Glow", [
            gradient_step("warm", "#FFBF00", "#FFF8F0", None)
        ])
    elif v == 4:
        return make_program("Bright Morning", [
            solid_step("main", "#FFF0E0", None)
        ])
    elif v == 5:
        return make_program("Morning Fresh", [
            wave_step("fresh", "#FFE4C4", "#F0F8FF", jitter(prompt, 3000), None)
        ])
    else:
        return make_program("Morning Warmth", [
            gradient_step("glow", "#D88B70", "#FFF0DC", None)
        ])

def gen_late_morning(prompt):
    """Late morning (10am-12pm). Bright, productive, clear."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Late Morning Focus", [
            solid_step("main", "#F0F8FF", None)
        ])
    elif v == 1:
        return make_program("Productive Morning", [
            gradient_step("focus", "#ADD8E6", "#F0F8FF", None)
        ])
    elif v == 2:
        return make_program("Clear Daylight", [
            solid_step("bright", "#FFFAF0", None)
        ])
    elif v == 3:
        return make_program("Morning Productivity", [
            gradient_step("work", "#F0F8FF", "#E6F0FF", None)
        ])
    else:
        return make_program("Bright Day", [
            solid_step("day", "#FFF8F0", None)
        ])

def gen_midday(prompt):
    """Midday/noon (12pm-2pm). Bright, energizing, possibly cool white."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("High Noon", [
            solid_step("bright", "#FFFFF0", None)
        ])
    elif v == 1:
        return make_program("Midday Bright", [
            gradient_step("sun", "#FFD700", "#FFFFF0", None)
        ])
    elif v == 2:
        return make_program("Noon Energy", [
            solid_step("main", "#FFF8E0", None)
        ])
    elif v == 3:
        return make_program("Lunchtime", [
            gradient_step("warm", "#FFE4C4", "#FFFFF0", None)
        ])
    else:
        return make_program("Peak Day", [
            solid_step("peak", "#F8F8FF", None)
        ])

def gen_afternoon(prompt):
    """Afternoon (2pm-5pm). Warm, slightly dimmer, combating slump."""
    h = prompt_hash(prompt)
    v = h % 7
    if v == 0:
        return make_program("Afternoon Boost", [
            breathing_step("pulse", "#FFD700", jitter(prompt, 2000), 10000),
            gradient_step("settle", "#F0F8FF", "#ADD8E6", None)
        ])
    elif v == 1:
        return make_program("Afternoon Energy", [
            wave_step("wake", "#FFD700", "#F0F8FF", jitter(prompt, 2500), None)
        ])
    elif v == 2:
        return make_program("Post-Lunch Refresh", [
            gradient_step("cool", "#ADD8E6", "#F0F8FF", None)
        ])
    elif v == 3:
        return make_program("Afternoon Light", [
            solid_step("bright", "#FFF0D0", None)
        ])
    elif v == 4:
        return make_program("Slump Buster", [
            pulse_step("wake", "#FFD700", 400, 1000),
            solid_step("bright", "#F0F8FF", None)
        ])
    elif v == 5:
        return make_program("Afternoon Warm", [
            gradient_step("sun", "#FFBF00", "#FFE4C4", None)
        ])
    else:
        return make_program("Golden Afternoon", [
            gradient_step("gold", "#FFD700", "#FFF8E8", None)
        ])

def gen_late_afternoon(prompt):
    """Late afternoon (4pm-6pm). Golden hour, warm tones."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Golden Hour", [
            gradient_step("gold", "#FF8C00", "#FFE4C4", None)
        ])
    elif v == 1:
        return make_program("Late Afternoon Glow", [
            wave_step("warm", "#FF6B4A", "#FFD700", jitter(prompt, 3500), None)
        ])
    elif v == 2:
        return make_program("Afternoon Fade", [
            gradient_step("warm", "#D88B70", "#FFE4C4", None)
        ])
    elif v == 3:
        return make_program("Pre-Sunset Warm", [
            gradient_step("gold", "#FFBF00", "#FFF0DC", None)
        ])
    else:
        return make_program("Fading Day", [
            breathing_step("warm", "#D88B70", jitter(prompt, 3000), None)
        ])

def gen_sunset(prompt):
    """Sunset/dusk (6pm-8pm). Warm oranges, pinks, transitional."""
    h = prompt_hash(prompt)
    v = h % 7
    if v == 0:
        return make_program("Sunset Glow", [
            gradient_step("sunset", "#FF6B4A", "#FFE4C4", 30000),
            gradient_step("dusk", "#D88B70", "#483D8B", None)
        ])
    elif v == 1:
        return make_program("Evening Transition", [
            wave_step("warm", "#FF6B4A", "#D88B70", jitter(prompt, 3000), 25000),
            gradient_step("settle", "#8B6B55", "#2a1a3a", None)
        ])
    elif v == 2:
        return make_program("Dusk Colors", [
            gradient_step("main", "#FF6B4A", "#9370DB", None)
        ])
    elif v == 3:
        return make_program("Sunset Transition", [
            gradient_step("orange", "#FF8C00", "#FF6B4A", 20000),
            gradient_step("purple", "#9370DB", "#483D8B", None)
        ])
    elif v == 4:
        return make_program("Evening Arrives", [
            breathing_step("warm", "#D88B70", jitter(prompt, 3500), None)
        ])
    elif v == 5:
        return make_program("Twilight Hour", [
            gradient_step("sky", "#FF6B4A", "#483D8B", None)
        ])
    else:
        return make_program("Sun Going Down", [
            wave_step("colors", "#FF8C00", "#9370DB", jitter(prompt, 4000), None)
        ])

def gen_evening(prompt):
    """Evening (8pm-10pm). Warm, cozy, relaxed, dimmer."""
    h = prompt_hash(prompt)
    v = h % 7
    if v == 0:
        return make_program("Evening Cozy", [
            gradient_step("warm", "#D88B70", "#8B6B55", None)
        ])
    elif v == 1:
        return make_program("Night Settling", [
            breathing_step("calm", "#D88B70", jitter(prompt, 4000), None)
        ])
    elif v == 2:
        return make_program("Evening Glow", [
            gradient_step("amber", "#FFBF00", "#8B6B55", None)
        ])
    elif v == 3:
        return make_program("Warm Evening", [
            solid_step("cozy", "#D88B70", None)
        ])
    elif v == 4:
        return make_program("Evening Wind Down", [
            breathing_step("soft", "#CC8866", jitter(prompt, 3500), None)
        ])
    elif v == 5:
        return make_program("Cozy Night", [
            gradient_step("warm", "#CC8866", "#6B4444", None)
        ])
    else:
        return make_program("Evening Ambiance", [
            wave_step("gentle", "#D88B70", "#8B5A44", jitter(prompt, 4500), None)
        ])

def gen_late_evening(prompt):
    """Late evening (10pm-12am). Very warm, dim, winding down."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Winding Down", [
            breathing_step("dim", "#8B6B55", jitter(prompt, 4500), None)
        ])
    elif v == 1:
        return make_program("Bedtime Dim", [
            gradient_step("low", "#6B4444", "#2a1a2a", None)
        ])
    elif v == 2:
        return make_program("Late Night Low", [
            solid_step("dim", "#5a3a2a", None)
        ])
    elif v == 3:
        return make_program("Night Glow", [
            breathing_step("gentle", "#6B4444", jitter(prompt, 5000), None)
        ])
    else:
        return make_program("Sleep Transition", [
            breathing_step("dim", "#483D8B", jitter(prompt, 5000), 30000),
            solid_step("sleep", "#1a1a2a", None)
        ])

def gen_night(prompt):
    """Night / late night (12am-3am). Very dim, blues/purples, calming."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Deep Night", [
            breathing_step("soft", "#191970", jitter(prompt, 5000), None)
        ])
    elif v == 1:
        return make_program("Midnight Glow", [
            solid_step("dim", "#1a1a3a", None)
        ])
    elif v == 2:
        return make_program("Late Night Calm", [
            gradient_step("night", "#0a0a2e", "#191970", None)
        ])
    elif v == 3:
        return make_program("Night Whisper", [
            breathing_step("low", "#2a1a4a", jitter(prompt, 6000), None)
        ])
    else:
        return make_program("Quiet Night", [
            solid_step("minimal", "#0d0d2b", None)
        ])

def gen_cant_sleep(prompt):
    """Can't sleep / insomnia. Ultra calming, very low."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Sleepless Calm", [
            breathing_step("soothe", "#191970", jitter(prompt, 6000), None)
        ])
    elif v == 1:
        return make_program("Insomnia Relief", [
            breathing_step("slow", "#1a1a4a", jitter(prompt, 7000), None)
        ])
    elif v == 2:
        return make_program("Can't Sleep", [
            gradient_step("dim", "#0a0a2e", "#1a1a3a", None)
        ])
    elif v == 3:
        return make_program("Restless Night", [
            breathing_step("calm", "#2a1a4a", jitter(prompt, 5500), None)
        ])
    else:
        return make_program("Sleep Aid", [
            breathing_step("deep", "#191970", jitter(prompt, 6500), 60000),
            solid_step("off", "#0a0a1a", None)
        ])

# ============================================================
# ACTIVITY-based response generators
# ============================================================

def gen_focus_work(prompt):
    """Focus/work/study. Cool whites, blues, clear."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Deep Focus", [
            solid_step("focus", "#F0F8FF", None)
        ])
    elif v == 1:
        return make_program("Work Mode", [
            gradient_step("focus", "#ADD8E6", "#F0F8FF", None)
        ])
    elif v == 2:
        return make_program("Study Light", [
            solid_step("bright", "#E8F0FF", None)
        ])
    elif v == 3:
        return make_program("Concentration", [
            gradient_step("clear", "#F0F8FF", "#E6F0FF", None)
        ])
    elif v == 4:
        return make_program("Task Light", [
            solid_step("main", "#F5F5FF", None)
        ])
    else:
        return make_program("Focus Zone", [
            solid_step("cool", "#E0EEFF", None)
        ])

def gen_relaxation(prompt):
    """Relaxation/unwinding. Warm, gentle, breathing patterns."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Unwind", [
            breathing_step("calm", "#D88B70", jitter(prompt, 4000), None)
        ])
    elif v == 1:
        return make_program("Relax Mode", [
            gradient_step("warm", "#D88B70", "#FFE4C4", None)
        ])
    elif v == 2:
        return make_program("Easy Evening", [
            breathing_step("soft", "#CC8866", jitter(prompt, 3500), None)
        ])
    elif v == 3:
        return make_program("Chill Vibes", [
            wave_step("gentle", "#D88B70", "#8B6B55", jitter(prompt, 4500), None)
        ])
    elif v == 4:
        return make_program("Decompress", [
            gradient_step("ease", "#CC8866", "#FFE4C4", None)
        ])
    else:
        return make_program("Wind Down", [
            breathing_step("warm", "#D88B70", jitter(prompt, 3800), None)
        ])

def gen_movie_tv(prompt):
    """Movie/TV watching. Dim, ambient, slight color."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Movie Night", [
            gradient_step("ambient", "#1a1a3a", "#2a1a4a", None)
        ])
    elif v == 1:
        return make_program("Cinema Mode", [
            solid_step("dim", "#1a1a2a", None)
        ])
    elif v == 2:
        return make_program("TV Ambient", [
            breathing_step("glow", "#2a2a4a", jitter(prompt, 5000), None)
        ])
    elif v == 3:
        return make_program("Watch Mode", [
            gradient_step("screen", "#191930", "#2a1a3a", None)
        ])
    elif v == 4:
        return make_program("Viewing Light", [
            solid_step("low", "#1a1a30", None)
        ])
    else:
        return make_program("Screen Time", [
            gradient_step("ambient", "#1a1030", "#2a2040", None)
        ])

def gen_cooking(prompt):
    """Cooking/kitchen. Bright, warm, functional."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Kitchen Light", [
            solid_step("bright", "#FFF0E0", None)
        ])
    elif v == 1:
        return make_program("Cooking Mode", [
            gradient_step("warm", "#FFE4C4", "#FFFFF0", None)
        ])
    elif v == 2:
        return make_program("Kitchen Warmth", [
            solid_step("task", "#FFF8E8", None)
        ])
    else:
        return make_program("Chef Light", [
            gradient_step("kitchen", "#FFBF00", "#FFF8F0", None)
        ])

def gen_meditation_yoga(prompt):
    """Meditation/yoga. Very calm, breathing patterns, soft colors."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Meditation", [
            breathing_step("om", "#4A90D9", jitter(prompt, 5000), None)
        ])
    elif v == 1:
        return make_program("Yoga Flow", [
            breathing_step("breath", "#008B8B", jitter(prompt, 4500), None)
        ])
    elif v == 2:
        return make_program("Zen Space", [
            gradient_step("peace", "#4A90D9", "#E6E6FA", None)
        ])
    elif v == 3:
        return make_program("Mindful Glow", [
            breathing_step("center", "#E6E6FA", jitter(prompt, 5500), None)
        ])
    elif v == 4:
        return make_program("Inner Peace", [
            breathing_step("calm", "#9370DB", jitter(prompt, 4800), None)
        ])
    else:
        return make_program("Stillness", [
            gradient_step("serene", "#008B8B", "#E6E6FA", None)
        ])

def gen_exercise(prompt):
    """Exercise/workout. Energetic, bright, pulsing."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Workout Mode", [
            wave_step("energy", "#FF4444", "#FFD700", jitter(prompt, 1500), None)
        ])
    elif v == 1:
        return make_program("Pump It Up", [
            breathing_step("power", "#FF4444", jitter(prompt, 1000), None)
        ])
    elif v == 2:
        return make_program("Get Moving", [
            pulse_step("start", "#FF4444", 300, 2000),
            wave_step("go", "#FF00FF", "#FFD700", jitter(prompt, 1200), None)
        ])
    elif v == 3:
        return make_program("Energy Boost", [
            solid_step("bright", "#FF4444", 5000),
            wave_step("move", "#FF4444", "#FF00FF", jitter(prompt, 1500), None)
        ])
    else:
        return make_program("Power Up", [
            rainbow_step("hype", jitter(prompt, 1500), None)
        ])

def gen_romantic(prompt):
    """Romantic. Soft pinks, reds, purples, dim."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Romantic Glow", [
            gradient_step("love", "#FFB6C1", "#9370DB", None)
        ])
    elif v == 1:
        return make_program("Date Night", [
            breathing_step("romance", "#FFB6C1", jitter(prompt, 3500), None)
        ])
    elif v == 2:
        return make_program("Love Light", [
            gradient_step("warm", "#8B0000", "#FFB6C1", None)
        ])
    elif v == 3:
        return make_program("Intimate", [
            wave_step("soft", "#FFB6C1", "#9370DB", jitter(prompt, 4000), None)
        ])
    elif v == 4:
        return make_program("Candlelight", [
            breathing_step("flicker", "#FF6B4A", jitter(prompt, 2500), None)
        ])
    else:
        return make_program("Romance Mode", [
            sparkle_step("stars", "#FFB6C1", "#2a0a1a", 150, 0.05, None)
        ])

def gen_party_social(prompt):
    """Party/social gathering. Fun, colorful, energetic or warm depending."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Party Mode", [
            rainbow_step("fun", jitter(prompt, 2000), None)
        ])
    elif v == 1:
        return make_program("Gathering Light", [
            gradient_step("warm", "#FFBF00", "#FFE4C4", None)
        ])
    elif v == 2:
        return make_program("Social Glow", [
            wave_step("vibe", "#FF6B4A", "#FFD700", jitter(prompt, 2500), None)
        ])
    elif v == 3:
        return make_program("Friends Over", [
            gradient_step("inviting", "#D88B70", "#FFE4C4", None)
        ])
    elif v == 4:
        return make_program("Get Together", [
            sparkle_step("festive", "#FFD700", "#2a1a0a", 120, 0.08, None)
        ])
    else:
        return make_program("Fun Night", [
            wave_step("party", "#FF00FF", "#00FFFF", jitter(prompt, 1800), None)
        ])

def gen_reading(prompt):
    """Reading. Warm white, not too bright, easy on eyes."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Reading Light", [
            solid_step("page", "#FFE8CC", None)
        ])
    elif v == 1:
        return make_program("Book Nook", [
            gradient_step("warm", "#FFE4C4", "#D88B70", None)
        ])
    elif v == 2:
        return make_program("Page Turner", [
            solid_step("soft", "#FFF0DC", None)
        ])
    elif v == 3:
        return make_program("Reading Glow", [
            gradient_step("gentle", "#FFD0A0", "#FFE8CC", None)
        ])
    else:
        return make_program("Story Light", [
            solid_step("read", "#FFECD0", None)
        ])

def gen_gaming(prompt):
    """Gaming. Dynamic, colorful, immersive."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Game On", [
            wave_step("dynamic", "#FF00FF", "#00FFFF", jitter(prompt, 1500), None)
        ])
    elif v == 1:
        return make_program("Gaming Mode", [
            gradient_step("cyber", "#FF00FF", "#0000FF", None)
        ])
    elif v == 2:
        return make_program("Player One", [
            sparkle_step("pixels", "#00FF00", "#0a0a2e", 80, 0.12, None)
        ])
    elif v == 3:
        return make_program("Game Session", [
            wave_step("glow", "#7B00FF", "#FF0055", jitter(prompt, 2000), None)
        ])
    else:
        return make_program("Level Up", [
            rainbow_step("rgb", jitter(prompt, 2000), None)
        ])

def gen_kids_family(prompt):
    """Kids/family activities. Cheerful, bright, playful."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Family Fun", [
            rainbow_step("play", jitter(prompt, 3000), None)
        ])
    elif v == 1:
        return make_program("Kids Time", [
            wave_step("playful", "#FFD700", "#FF6B4A", jitter(prompt, 2500), None)
        ])
    elif v == 2:
        return make_program("Cheerful Light", [
            gradient_step("happy", "#FFD700", "#FF6B4A", None)
        ])
    elif v == 3:
        return make_program("Playtime", [
            sparkle_step("twinkle", "#FFD700", "#FFF8E0", 100, 0.08, None)
        ])
    else:
        return make_program("Fun Times", [
            solid_step("bright", "#FFE8C0", None)
        ])

def gen_baby_nursery(prompt):
    """Baby/nursery. Ultra soft, very dim, warm or cool pastels."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Nursery Glow", [
            breathing_step("soft", "#E6E6FA", jitter(prompt, 5000), None)
        ])
    elif v == 1:
        return make_program("Baby Light", [
            solid_step("dim", "#FFE8CC", None)
        ])
    elif v == 2:
        return make_program("Lullaby", [
            breathing_step("gentle", "#FFB6C1", jitter(prompt, 5500), None)
        ])
    elif v == 3:
        return make_program("Night Light", [
            gradient_step("soft", "#E6E6FA", "#FFE4C4", None)
        ])
    else:
        return make_program("Nursery Calm", [
            breathing_step("soothe", "#CCCCFF", jitter(prompt, 6000), None)
        ])

def gen_creative(prompt):
    """Creative activities (art, music, writing, crafts). Inspiring, warm or natural."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Creative Flow", [
            gradient_step("inspire", "#9370DB", "#FFB6C1", None)
        ])
    elif v == 1:
        return make_program("Art Studio", [
            solid_step("natural", "#FFF8F0", None)
        ])
    elif v == 2:
        return make_program("Inspiration", [
            wave_step("muse", "#9370DB", "#4A90D9", jitter(prompt, 3500), None)
        ])
    elif v == 3:
        return make_program("Create Mode", [
            gradient_step("flow", "#4A90D9", "#E6E6FA", None)
        ])
    elif v == 4:
        return make_program("Maker Light", [
            solid_step("bright", "#FFF0E8", None)
        ])
    else:
        return make_program("Studio Vibe", [
            gradient_step("warm", "#FFE4C4", "#F0F8FF", None)
        ])

def gen_task_light(prompt):
    """Task lighting (cleaning, organizing, assembling). Very bright, functional."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Task Bright", [
            solid_step("work", "#FFFFF0", None)
        ])
    elif v == 1:
        return make_program("Bright Task", [
            solid_step("clear", "#F8F8FF", None)
        ])
    elif v == 2:
        return make_program("Full Bright", [
            solid_step("max", "#FFFFFF", None)
        ])
    else:
        return make_program("Work Light", [
            gradient_step("task", "#FFFFF0", "#F0F8FF", None)
        ])

def gen_video_call(prompt):
    """Video call/presentation. Good face lighting, neutral, bright enough."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Video Call", [
            solid_step("face", "#FFF0E0", None)
        ])
    elif v == 1:
        return make_program("On Camera", [
            gradient_step("flattering", "#FFE4C4", "#FFF8F0", None)
        ])
    elif v == 2:
        return make_program("Meeting Light", [
            solid_step("professional", "#FFF8F0", None)
        ])
    else:
        return make_program("Presentation", [
            solid_step("bright", "#FFFAF0", None)
        ])

def gen_sleep(prompt):
    """Sleep/bedtime. Ultra dim, fading to near-off."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Sleep Mode", [
            breathing_step("fade", "#191970", jitter(prompt, 6000), 60000),
            solid_step("off", "#050510", None)
        ])
    elif v == 1:
        return make_program("Dreamland", [
            breathing_step("drift", "#1a1a3a", jitter(prompt, 7000), None)
        ])
    elif v == 2:
        return make_program("Goodnight", [
            gradient_step("dim", "#1a1a3a", "#0a0a1a", None)
        ])
    elif v == 3:
        return make_program("Lights Out", [
            breathing_step("fade", "#191970", jitter(prompt, 5500), 45000),
            solid_step("dark", "#0a0a0a", None)
        ])
    else:
        return make_program("Sweet Dreams", [
            solid_step("minimal", "#0a0a1a", None)
        ])

def gen_calming(prompt):
    """Calming/anxiety relief. Slow breathing, blues, lavender."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Calm Down", [
            breathing_step("peace", "#4A90D9", jitter(prompt, 5000), None)
        ])
    elif v == 1:
        return make_program("Soothing Light", [
            breathing_step("gentle", "#E6E6FA", jitter(prompt, 5500), None)
        ])
    elif v == 2:
        return make_program("Anxiety Relief", [
            breathing_step("slow", "#008B8B", jitter(prompt, 6000), None)
        ])
    elif v == 3:
        return make_program("Peace", [
            gradient_step("calm", "#4A90D9", "#E6E6FA", None)
        ])
    elif v == 4:
        return make_program("Tranquil", [
            wave_step("soothe", "#4A90D9", "#E6E6FA", jitter(prompt, 5000), None)
        ])
    else:
        return make_program("Safe Space", [
            breathing_step("hold", "#9370DB", jitter(prompt, 4500), None)
        ])

def gen_horror_spooky(prompt):
    """Horror/spooky. Dark, flickering, eerie."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Spooky Mode", [
            sparkle_step("flicker", "#FF2200", "#0a0a0a", 60, 0.04, 5000),
            solid_step("dark", "#0a0a0a", 3000),
            pulse_step("flash", "#FFFFFF", 200, 500)
        ], {"count": 0, "start_step": "flicker", "end_step": "flash"})
    elif v == 1:
        return make_program("Horror Night", [
            breathing_step("eerie", "#330000", jitter(prompt, 4000), 6000),
            pulse_step("jump", "#FF0000", 200, 500),
            solid_step("dark", "#0a0000", 4000)
        ], {"count": 0, "start_step": "eerie", "end_step": "dark"})
    elif v == 2:
        return make_program("Creepy Glow", [
            breathing_step("ominous", "#220022", jitter(prompt, 5000), None)
        ])
    else:
        return make_program("Dark Watch", [
            gradient_step("shadow", "#0a0000", "#1a0000", None)
        ])

def gen_nap(prompt):
    """Nap/power nap. Quick fade to very dim."""
    h = prompt_hash(prompt)
    v = h % 3
    if v == 0:
        return make_program("Power Nap", [
            breathing_step("drift", "#483D8B", jitter(prompt, 5000), 30000),
            solid_step("dark", "#0a0a1a", None)
        ])
    elif v == 1:
        return make_program("Quick Nap", [
            breathing_step("sleep", "#191970", jitter(prompt, 6000), None)
        ])
    else:
        return make_program("Nap Time", [
            gradient_step("dim", "#2a1a3a", "#0a0a1a", None)
        ])

def gen_bath_spa(prompt):
    """Bath/spa. Warm, soothing, lavender/teal tones."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Spa Mode", [
            breathing_step("bliss", "#008B8B", jitter(prompt, 4500), None)
        ])
    elif v == 1:
        return make_program("Bath Time", [
            gradient_step("warm", "#E6E6FA", "#FFB6C1", None)
        ])
    elif v == 2:
        return make_program("Spa Retreat", [
            wave_step("flow", "#008B8B", "#E6E6FA", jitter(prompt, 4000), None)
        ])
    elif v == 3:
        return make_program("Relaxation", [
            breathing_step("lavender", "#E6E6FA", jitter(prompt, 4000), None)
        ])
    else:
        return make_program("Pamper Mode", [
            gradient_step("soothe", "#008B8B", "#FFB6C1", None)
        ])

def gen_celebration(prompt):
    """Celebration/party/birthday. Colorful, energetic, festive."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Celebration", [
            rainbow_step("party", jitter(prompt, 1800), None)
        ])
    elif v == 1:
        return make_program("Party Time", [
            sparkle_step("confetti", "#FFD700", "#FF00FF", 80, 0.15, 5000),
            wave_step("dance", "#FF00FF", "#00FFFF", 1500, 5000)
        ], {"count": 0, "start_step": "confetti", "end_step": "dance"})
    elif v == 2:
        return make_program("Festive", [
            wave_step("color", "#FF4444", "#FFD700", jitter(prompt, 1500), None)
        ])
    elif v == 3:
        return make_program("Let's Go", [
            sparkle_step("sparkle", "#FFFFFF", "#FF00FF", 60, 0.12, None)
        ])
    else:
        return make_program("Fiesta", [
            rainbow_step("bright", jitter(prompt, 2000), None)
        ])

def gen_nature_garden(prompt):
    """Nature/gardening. Greens, earth tones, natural light."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Green Vibes", [
            gradient_step("nature", "#228B22", "#90EE90", None)
        ])
    elif v == 1:
        return make_program("Garden Light", [
            wave_step("leaves", "#228B22", "#8B4513", jitter(prompt, 3500), None)
        ])
    elif v == 2:
        return make_program("Natural Glow", [
            solid_step("green", "#90EE90", None)
        ])
    else:
        return make_program("Earthy", [
            gradient_step("earth", "#8B4513", "#228B22", None)
        ])

def gen_nostalgia(prompt):
    """Nostalgia/memories. Warm amber, gentle, wistful."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Memory Lane", [
            breathing_step("warm", "#FFBF00", jitter(prompt, 3500), None)
        ])
    elif v == 1:
        return make_program("Nostalgic Glow", [
            gradient_step("amber", "#FFBF00", "#D88B70", None)
        ])
    elif v == 2:
        return make_program("Golden Memories", [
            breathing_step("soft", "#D88B70", jitter(prompt, 4000), None)
        ])
    else:
        return make_program("Remember When", [
            gradient_step("warm", "#CC8866", "#FFE4C4", None)
        ])

def gen_waiting(prompt):
    """Waiting/idle. Gentle, ambient, not demanding attention."""
    h = prompt_hash(prompt)
    v = h % 3
    if v == 0:
        return make_program("Idle Glow", [
            breathing_step("wait", "#4A90D9", jitter(prompt, 4000), None)
        ])
    elif v == 1:
        return make_program("Background Light", [
            gradient_step("ambient", "#D88B70", "#FFE4C4", None)
        ])
    else:
        return make_program("Standby", [
            breathing_step("gentle", "#E6E6FA", jitter(prompt, 3500), None)
        ])

def gen_night_sky(prompt):
    """Night sky/stars. Dark with sparkles."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Starry Night", [
            sparkle_step("stars", "#FFFFFF", "#0a0a2e", 150, 0.06, None)
        ])
    elif v == 1:
        return make_program("Night Sky", [
            sparkle_step("twinkle", "#FFF8E0", "#0a0a1a", 200, 0.05, None)
        ])
    elif v == 2:
        return make_program("Cosmos", [
            sparkle_step("galaxy", "#E6E6FA", "#0a0a2e", 180, 0.07, None)
        ])
    else:
        return make_program("Under Stars", [
            sparkle_step("sky", "#FFFFFF", "#191970", 160, 0.04, None)
        ])

def gen_cozy(prompt):
    """Cozy/safe/warm feeling. Warm gradients, gentle."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Cozy Cocoon", [
            gradient_step("warm", "#D88B70", "#FFE4C4", None)
        ])
    elif v == 1:
        return make_program("Warm Hug", [
            breathing_step("snug", "#D88B70", jitter(prompt, 3500), None)
        ])
    elif v == 2:
        return make_program("Safe Haven", [
            gradient_step("cozy", "#FF6B4A", "#FFE4C4", None)
        ])
    elif v == 3:
        return make_program("Comfort Zone", [
            solid_step("warm", "#D88B70", None)
        ])
    else:
        return make_program("Snuggle Light", [
            gradient_step("amber", "#FFBF00", "#FFE4C4", None)
        ])

def gen_music(prompt):
    """Music-related. Atmospheric, mood-dependent."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Music Mood", [
            wave_step("rhythm", "#9370DB", "#4A90D9", jitter(prompt, 2500), None)
        ])
    elif v == 1:
        return make_program("Concert Light", [
            gradient_step("stage", "#FF00FF", "#4A00FF", None)
        ])
    elif v == 2:
        return make_program("Jam Session", [
            wave_step("groove", "#FF6B4A", "#FFD700", jitter(prompt, 2000), None)
        ])
    elif v == 3:
        return make_program("Musical Glow", [
            breathing_step("tempo", "#9370DB", jitter(prompt, 3000), None)
        ])
    else:
        return make_program("Studio Light", [
            gradient_step("vibe", "#FF00FF", "#00FFFF", None)
        ])

def gen_christmas(prompt):
    """Christmas/holiday. Red, green, warm, festive."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Christmas Glow", [
            wave_step("holiday", "#FF0000", "#00CC00", jitter(prompt, 2500), None)
        ])
    elif v == 1:
        return make_program("Holiday Spirit", [
            sparkle_step("twinkle", "#FFD700", "#1a3a1a", 120, 0.08, None)
        ])
    elif v == 2:
        return make_program("Festive Season", [
            gradient_step("xmas", "#CC0000", "#006600", None)
        ])
    else:
        return make_program("Merry Lights", [
            wave_step("festive", "#FF0000", "#FFD700", jitter(prompt, 2000), None)
        ])

# ============================================================
# EMOTION-based response generators
# ============================================================

def gen_happy(prompt):
    """Happy/joyful/excited. Warm, bright, energetic."""
    h = prompt_hash(prompt)
    v = h % 6
    if v == 0:
        return make_program("Joy", [
            wave_step("happy", "#FFD700", "#FF6B4A", jitter(prompt, 2000), None)
        ])
    elif v == 1:
        return make_program("Happiness", [
            rainbow_step("celebrate", jitter(prompt, 2500), None)
        ])
    elif v == 2:
        return make_program("Bright Joy", [
            gradient_step("sunny", "#FFD700", "#FF6B4A", None)
        ])
    elif v == 3:
        return make_program("Good Vibes", [
            sparkle_step("glow", "#FFD700", "#FFF8E0", 100, 0.08, None)
        ])
    elif v == 4:
        return make_program("Elation", [
            wave_step("burst", "#FF00FF", "#FFD700", jitter(prompt, 1800), None)
        ])
    else:
        return make_program("Sunny Mood", [
            solid_step("bright", "#FFD700", None)
        ])

def gen_sad(prompt):
    """Sad/down/depressed. Gentle blues, comforting warm tones."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Gentle Comfort", [
            breathing_step("soft", "#4A90D9", jitter(prompt, 4500), None)
        ])
    elif v == 1:
        return make_program("Blue Hour", [
            gradient_step("quiet", "#4A90D9", "#E6E6FA", None)
        ])
    elif v == 2:
        return make_program("Comfort Light", [
            breathing_step("warm", "#D88B70", jitter(prompt, 4000), None)
        ])
    elif v == 3:
        return make_program("Soft Blue", [
            breathing_step("soothe", "#483D8B", jitter(prompt, 5000), None)
        ])
    else:
        return make_program("Quiet Glow", [
            gradient_step("gentle", "#9370DB", "#E6E6FA", None)
        ])

def gen_angry(prompt):
    """Angry/frustrated. Start intense then transition to calming."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Cool Down", [
            breathing_step("slow", "#4A90D9", jitter(prompt, 4000), None)
        ])
    elif v == 1:
        return make_program("Release", [
            pulse_step("vent", "#FF4444", 500, 3000),
            breathing_step("calm", "#4A90D9", 4500, None)
        ])
    elif v == 2:
        return make_program("Steady Calm", [
            breathing_step("peace", "#008B8B", jitter(prompt, 5000), None)
        ])
    else:
        return make_program("Let Go", [
            wave_step("soothe", "#4A90D9", "#008B8B", jitter(prompt, 4000), None)
        ])

def gen_anxious(prompt):
    """Anxious/nervous/overwhelmed. Slow, grounding, calming."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Ground Yourself", [
            breathing_step("earth", "#008B8B", jitter(prompt, 5000), None)
        ])
    elif v == 1:
        return make_program("Calm Waves", [
            wave_step("slow", "#4A90D9", "#E6E6FA", jitter(prompt, 5000), None)
        ])
    elif v == 2:
        return make_program("Breathing Room", [
            breathing_step("inhale", "#4A90D9", jitter(prompt, 5500), None)
        ])
    elif v == 3:
        return make_program("Safe Glow", [
            gradient_step("comfort", "#D88B70", "#FFE4C4", None)
        ])
    else:
        return make_program("Steady Light", [
            breathing_step("ground", "#E6E6FA", jitter(prompt, 4500), None)
        ])

def gen_energetic(prompt):
    """Energetic/hyped/pumped. Bright, dynamic, fast patterns."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Full Energy", [
            wave_step("hype", "#FF4444", "#FFD700", jitter(prompt, 1200), None)
        ])
    elif v == 1:
        return make_program("Fired Up", [
            rainbow_step("go", jitter(prompt, 1500), None)
        ])
    elif v == 2:
        return make_program("High Voltage", [
            wave_step("electric", "#FF00FF", "#00FFFF", jitter(prompt, 1000), None)
        ])
    elif v == 3:
        return make_program("Power Mode", [
            sparkle_step("flash", "#FFFFFF", "#FF4444", 50, 0.15, None)
        ])
    else:
        return make_program("Let's Go", [
            wave_step("pump", "#FF4444", "#FF00FF", jitter(prompt, 1300), None)
        ])

def gen_peaceful(prompt):
    """Peaceful/content/zen. Soft, still, natural tones."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Inner Peace", [
            gradient_step("serene", "#E6E6FA", "#F0F8FF", None)
        ])
    elif v == 1:
        return make_program("Contentment", [
            breathing_step("slow", "#008B8B", jitter(prompt, 5000), None)
        ])
    elif v == 2:
        return make_program("Zen", [
            gradient_step("balance", "#4A90D9", "#E6E6FA", None)
        ])
    elif v == 3:
        return make_program("Tranquility", [
            solid_step("peace", "#E6E6FA", None)
        ])
    else:
        return make_program("Stillness", [
            breathing_step("gentle", "#E6E6FA", jitter(prompt, 4800), None)
        ])

def gen_creative_mood(prompt):
    """Creative/inspired. Purples, dynamic, flowing."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Creative Spark", [
            wave_step("flow", "#9370DB", "#FF6B4A", jitter(prompt, 2500), None)
        ])
    elif v == 1:
        return make_program("Inspiration", [
            gradient_step("muse", "#9370DB", "#FFB6C1", None)
        ])
    elif v == 2:
        return make_program("Imagination", [
            sparkle_step("ideas", "#FFD700", "#2a1a4a", 100, 0.08, None)
        ])
    else:
        return make_program("Creative Fire", [
            wave_step("vision", "#FF00FF", "#FFD700", jitter(prompt, 2000), None)
        ])

def gen_lonely(prompt):
    """Lonely/homesick. Warm, comforting, gentle embrace."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Warm Embrace", [
            breathing_step("hold", "#D88B70", jitter(prompt, 4000), None)
        ])
    elif v == 1:
        return make_program("You're Not Alone", [
            gradient_step("comfort", "#FFB6C1", "#FFE4C4", None)
        ])
    elif v == 2:
        return make_program("Gentle Company", [
            breathing_step("soft", "#CC8866", jitter(prompt, 3800), None)
        ])
    else:
        return make_program("Comfort Glow", [
            gradient_step("warm", "#D88B70", "#FFE4C4", None)
        ])

def gen_bored(prompt):
    """Bored/restless. Something visually interesting."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Eye Candy", [
            rainbow_step("mesmerize", jitter(prompt, 2500), None)
        ])
    elif v == 1:
        return make_program("Something Fun", [
            wave_step("play", "#FF00FF", "#00FFFF", jitter(prompt, 2000), None)
        ])
    elif v == 2:
        return make_program("Visual Treat", [
            sparkle_step("dazzle", "#FFD700", "#1a1a3a", 80, 0.12, None)
        ])
    else:
        return make_program("Watch This", [
            wave_step("mesmerize", "#FF6B4A", "#4A90D9", jitter(prompt, 2200), 8000),
            sparkle_step("sparkle", "#FFFFFF", "#2a1a4a", 100, 0.1, 8000)
        ], {"count": 0, "start_step": "mesmerize", "end_step": "sparkle"})

def gen_mysterious(prompt):
    """Mysterious/noir. Deep purples, dark, atmospheric."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Noir", [
            gradient_step("shadow", "#1a0a2a", "#3a1a4a", None)
        ])
    elif v == 1:
        return make_program("Mystery", [
            breathing_step("dark", "#2a1a4a", jitter(prompt, 4000), None)
        ])
    elif v == 2:
        return make_program("Enigma", [
            sparkle_step("glimmer", "#9370DB", "#0a0a1a", 200, 0.03, None)
        ])
    else:
        return make_program("Shadow Play", [
            wave_step("dark", "#2a1a4a", "#0a0a1a", jitter(prompt, 5000), None)
        ])

def gen_proud(prompt):
    """Proud/accomplished. Warm, golden, triumphant."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Achievement", [
            gradient_step("gold", "#FFD700", "#FFBF00", None)
        ])
    elif v == 1:
        return make_program("Victory Glow", [
            wave_step("triumph", "#FFD700", "#FF6B4A", jitter(prompt, 2000), None)
        ])
    elif v == 2:
        return make_program("Well Done", [
            sparkle_step("celebrate", "#FFD700", "#FFF0C0", 100, 0.08, None)
        ])
    else:
        return make_program("Golden Moment", [
            solid_step("proud", "#FFD700", None)
        ])

def gen_gentle_emotional(prompt):
    """Tender/vulnerable/sentimental. Very soft, warm, safe."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Tender Light", [
            breathing_step("soft", "#FFB6C1", jitter(prompt, 4500), None)
        ])
    elif v == 1:
        return make_program("Gentle Glow", [
            gradient_step("tender", "#FFB6C1", "#E6E6FA", None)
        ])
    elif v == 2:
        return make_program("Soft Embrace", [
            breathing_step("warm", "#D88B70", jitter(prompt, 4000), None)
        ])
    elif v == 3:
        return make_program("Safe Light", [
            gradient_step("comfort", "#E6E6FA", "#FFE4C4", None)
        ])
    else:
        return make_program("Holding Space", [
            breathing_step("gentle", "#E6E6FA", jitter(prompt, 5000), None)
        ])

def gen_determined(prompt):
    """Determined/focused. Clear, bright, strong."""
    h = prompt_hash(prompt)
    v = h % 4
    if v == 0:
        return make_program("Determination", [
            solid_step("clear", "#F0F8FF", None)
        ])
    elif v == 1:
        return make_program("Unstoppable", [
            gradient_step("sharp", "#ADD8E6", "#F0F8FF", None)
        ])
    elif v == 2:
        return make_program("Locked In", [
            solid_step("focus", "#E8F0FF", None)
        ])
    else:
        return make_program("Drive Mode", [
            gradient_step("clear", "#F0F8FF", "#FFFFFF", None)
        ])

def gen_playful(prompt):
    """Playful/silly/whimsical. Fun colors, movement."""
    h = prompt_hash(prompt)
    v = h % 5
    if v == 0:
        return make_program("Playful Mode", [
            rainbow_step("fun", jitter(prompt, 2000), None)
        ])
    elif v == 1:
        return make_program("Silly Lights", [
            wave_step("wiggle", "#FF00FF", "#00FF88", jitter(prompt, 1500), None)
        ])
    elif v == 2:
        return make_program("Fun Time", [
            sparkle_step("play", "#FFD700", "#FF00FF", 80, 0.12, None)
        ])
    elif v == 3:
        return make_program("Whimsy", [
            wave_step("bounce", "#FFD700", "#FF6B4A", jitter(prompt, 1800), None)
        ])
    else:
        return make_program("Giggles", [
            rainbow_step("dance", jitter(prompt, 2200), None)
        ])

def gen_mourning(prompt):
    """Grief/mourning. Very gentle, respectful, soft warm light."""
    h = prompt_hash(prompt)
    v = h % 3
    if v == 0:
        return make_program("Quiet Light", [
            breathing_step("gentle", "#E6E6FA", jitter(prompt, 6000), None)
        ])
    elif v == 1:
        return make_program("Soft Presence", [
            solid_step("warm", "#D88B70", None)
        ])
    else:
        return make_program("Holding Space", [
            breathing_step("slow", "#CC8866", jitter(prompt, 5500), None)
        ])


# ============================================================
# KEYWORD MATCHING + CLASSIFICATION
# ============================================================

def classify_and_generate(prompt):
    """Classify a prompt and generate an appropriate lamp program response."""
    p = prompt.lower().strip()

    # --- EMOTION-BASED (check first since they're specific) ---
    if any(w in p for w in ['anxious', 'anxiety', 'panic attack', 'overwhelmed', 'nervous', 'stressed']):
        return gen_anxious(prompt)
    if any(w in p for w in ['angry', 'furious', 'frustrated', 'irritated', 'annoying', 'scream']):
        return gen_angry(prompt)
    if any(w in p for w in ['sad', 'down today', 'depressed', 'mourning', 'lost someone']):
        if 'mourning' in p or 'lost someone' in p:
            return gen_mourning(prompt)
        return gen_sad(prompt)
    if any(w in p for w in ['lonely', 'homesick', 'alone', 'miss', 'missing home', 'disconnected']):
        return gen_lonely(prompt)
    if any(w in p for w in ['happy', 'great news', 'joyful', 'giddy', 'christmas morning', 'bursting', 'elation']):
        return gen_happy(prompt)
    if any(w in p for w in ['energetic', 'hyped', 'pumped', 'fired up', 'competitive', 'high energy']):
        return gen_energetic(prompt)
    if any(w in p for w in ['peaceful', 'content', 'zen', 'aligned', 'relaxed i could melt', 'everything feels right']):
        return gen_peaceful(prompt)
    if any(w in p for w in ['creative', 'inspired', 'creative energy', 'imagination']):
        return gen_creative_mood(prompt)
    if any(w in p for w in ['proud', 'accomplished', 'finished a big project']):
        return gen_proud(prompt)
    if any(w in p for w in ['bored', 'entertain me', 'restless']):
        return gen_bored(prompt)
    if any(w in p for w in ['mysterious', 'noir']):
        return gen_mysterious(prompt)
    if any(w in p for w in ['playful', 'silly', 'whimsical', 'fun ']):
        return gen_playful(prompt)
    if any(w in p for w in ['determined', 'focused', 'nothing stopping', 'locked in']):
        return gen_determined(prompt)
    if any(w in p for w in ['vulnerable', 'tender', 'emotional', 'sentimental', 'insecure', 'gentle', 'need a hug',
                             'feeling small', 'good cry', 'lighter now', 'spacey', 'daydream', 'generous',
                             'warm towards', 'grateful', 'thankful', 'hopeful']):
        return gen_gentle_emotional(prompt)
    if any(w in p for w in ['in a funk', 'cheering up', 'cheer me']):
        return gen_happy(prompt)
    if any(w in p for w in ['calm me', 'calm down', 'need to calm', 'soothing']):
        return gen_calming(prompt)
    if any(w in p for w in ['excited', "can't sit still"]):
        return gen_happy(prompt)
    if any(w in p for w in ['contemplat', 'thoughtful', 'thinking', 'deep thought']):
        return gen_peaceful(prompt)
    if any(w in p for w in ['confused', 'scattered', 'help me focus']):
        return gen_focus_work(prompt)
    if any(w in p for w in ['romantic tonight', 'romantic']):
        return gen_romantic(prompt)
    if any(w in p for w in ['tired but not sleepy']):
        return gen_relaxation(prompt)

    # --- ACTIVITY-BASED ---
    if any(w in p for w in ['horror', 'scary movie', 'scary series']):
        return gen_horror_spooky(prompt)
    if any(w in p for w in ['meditation', 'meditat', 'yoga', 'pilates', 'breathing exercise', 'deep breath',
                             'stretching before bed', 'light stretching']):
        return gen_meditation_yoga(prompt)
    if any(w in p for w in ['workout', 'exercise', 'push-ups', 'squats', 'plank', 'core work', 'gym',
                             'home workout', 'run,', 'finished a run']):
        return gen_exercise(prompt)
    if any(w in p for w in ['romantic dinner', 'date night', 'slow dance', 'fondue', 'romantic movie']):
        return gen_romantic(prompt)
    if any(w in p for w in ['party', 'karaoke', 'birthday', 'baby shower', 'celebration', 'potluck',
                             'girls\' night', 'friends over', 'gathering', 'board game', 'charades',
                             'game night', 'happy hour', 'wine and cheese', 'cocktails']):
        return gen_party_social(prompt)
    if any(w in p for w in ['video call', 'zoom', 'presentation', 'online interview', 'standup call',
                             'team standup', 'meeting']):
        return gen_video_call(prompt)
    if any(w in p for w in ['movie', 'netflix', 'tv series', 'documentary', 'binge watch', 'watching',
                             'trash tv', 'thriller movie', 'movie marathon', 'asmr']):
        return gen_movie_tv(prompt)
    if any(w in p for w in ['gaming', 'video game', 'rpg', 'co-op', 'escape room']):
        return gen_gaming(prompt)
    if any(w in p for w in ['reading', 'book', 'comics', 'novel', 'newspaper']):
        return gen_reading(prompt)
    if any(w in p for w in ['cooking', 'baking', 'kitchen', 'recipe', 'pasta', 'cookies', 'frosting',
                             'meal prep', 'fridge']):
        return gen_cooking(prompt)
    if any(w in p for w in ['bath', 'spa', 'facial', 'face mask', 'skincare', 'shower', 'pamper', 'nails']):
        return gen_bath_spa(prompt)
    if any(w in p for w in ['nap', 'power nap']):
        return gen_nap(prompt)
    if any(w in p for w in ['baby', 'nursery', 'feeding the baby', 'newborn', 'toddler']):
        return gen_baby_nursery(prompt)
    if any(w in p for w in ['kid', 'children', 'playdate', 'blanket fort', 'hide and seek', 'school',
                             'building blocks', 'science fair', 'bedtime story', 'sleepover']):
        return gen_kids_family(prompt)
    if any(w in p for w in ['paint', 'sketch', 'draw', 'art project', 'watercolor', 'bob ross']):
        return gen_creative(prompt)
    if any(w in p for w in ['guitar', 'piano', 'music', 'vinyl', 'mixing', 'singing', 'concert']):
        return gen_music(prompt)
    if any(w in p for w in ['writing', 'journal', 'poetry', 'gratitude', 'novel', 'thank you card',
                             'coloring', 'scrapbook', 'origami', 'crochet', 'knitting', 'sewing',
                             'diamond painting', 'friendship bracelet', 'lego', 'model kit', 'puzzle',
                             'crossword', 'jigsaw']):
        return gen_creative(prompt)
    if any(w in p for w in ['study', 'focus', 'homework', 'report', 'deadline', 'crunch', 'debug',
                             'code', 'grading', 'resume', 'language', 'flash card', 'online class',
                             'tutoring', 'email']):
        return gen_focus_work(prompt)
    if any(w in p for w in ['cleaning', 'organizing', 'declutter', 'laundry', 'ironing', 'assembl',
                             'furniture', 'bookshelf', 'fixing', 'repotting', 'dishes']):
        return gen_task_light(prompt)
    if any(w in p for w in ['garden', 'plant', 'seeds', 'watering']):
        return gen_nature_garden(prompt)
    if any(w in p for w in ['christmas', 'tree', 'decorat']):
        return gen_christmas(prompt)
    if any(w in p for w in ['nostalg', 'yearbook', 'old photo', 'remember']):
        return gen_nostalgia(prompt)
    if any(w in p for w in ['waiting', 'on hold', 'customer service']):
        return gen_waiting(prompt)
    if any(w in p for w in ['night sky', 'stars are out', 'starry']):
        return gen_night_sky(prompt)
    if any(w in p for w in ['cozy', 'safe', 'snug', 'comfort', 'warm']):
        return gen_cozy(prompt)
    if any(w in p for w in ['pray', 'reverent', 'tarot']):
        return gen_meditation_yoga(prompt)
    if any(w in p for w in ['podcast', 'recording', 'youtube', 'voice memo']):
        return gen_video_call(prompt)
    if any(w in p for w in ['sleep', 'bedtime', 'go to bed', 'asleep', 'tucking in', 'night mode',
                             'lights out', 'goodnight', 'dimming']):
        return gen_sleep(prompt)
    if any(w in p for w in ['unwind', 'relax', 'wind down', 'decompres', 'settling', 'chill',
                             'unwinding', 'cool down', 'settling in']):
        return gen_relaxation(prompt)
    if any(w in p for w in ['phone', 'scroll', 'mindless']):
        return gen_relaxation(prompt)
    if any(w in p for w in ['packing', 'trip']):
        return gen_task_light(prompt)
    if any(w in p for w in ['play', 'dog', 'cat', 'pet']):
        return gen_kids_family(prompt)
    if any(w in p for w in ['unbox', 'tech', 'gadget']):
        return gen_task_light(prompt)
    if any(w in p for w in ['eating', 'dinner alone', 'dinner time', 'table', 'breakfast', 'brunch',
                             'lunch', 'meal', 'appetizer', 'tea']):
        return gen_cooking(prompt)
    if any(w in p for w in ['just got home', 'end of work', 'after work', 'post-work', 'leaving work',
                             'wrapping up work', 'shutting the laptop']):
        return gen_relaxation(prompt)

    # --- TIME-OF-DAY BASED ---
    if any(w in p for w in ["can't sleep", 'insomnia', 'still awake', "here i am", "should be asleep",
                             "know i should sleep", "whatever"]):
        return gen_cant_sleep(prompt)
    if any(w in p for w in ['3am', '4am', '3 am', '4 am', '2am', '2 am', '1am', '1 am',
                             'wee hours', 'middle of the night', 'way too early',
                             'past midnight', 'post-midnight', 'witching hour',
                             'hours before dawn', 'dead quiet', '12:30am', '1:30am',
                             "so late it's almost early", 'really late']):
        return gen_night(prompt)
    if any(w in p for w in ['5am', '5 am', '4:30am', '5:30am', 'crack of dawn', 'before dawn',
                             'pre-dawn', "before the sun", 'roosters', 'early early',
                             "birds aren't even up", "dark thirty", "haven't seen the sun",
                             'barely dawn']):
        return gen_dawn(prompt)
    if any(w in p for w in ['6am', '6 am', '6:30', 'sunrise', 'dawn', 'first light',
                             'sun coming up', 'just turning pink', 'day is just starting',
                             'daybreak', 'sun just came up', 'the day is brand new',
                             'just before the sun comes up', 'morning light is gorgeous',
                             'fresh new morning']):
        return gen_dawn(prompt)
    if any(w in p for w in ['7am', '7 am', '7:30', '7:45', '8am', '8 am', '8:30',
                             'wake up', 'woke up', 'getting ready', 'morning coffee',
                             'breakfast', 'morning rush', 'morning person',
                             'getting the kids ready', 'just having breakfast',
                             'head out the door', 'morning shower', 'bright morning']):
        return gen_morning(prompt)
    if any(w in p for w in ['9am', '9 am', '10am', '10 am', '10:30', '11am', '11 am',
                             'mid-morning', 'late morning', 'brunch', 'productivity',
                             'focus time', 'work mode']):
        return gen_late_morning(prompt)
    if any(w in p for w in ['noon', '12pm', '12 pm', 'midday', 'lunchtime', '12:30',
                             'half past noon', 'just past lunch']):
        return gen_midday(prompt)
    if any(w in p for w in ['1pm', '1 pm', '2pm', '2 pm', '2:30', '3pm', '3 pm', '3:30',
                             'afternoon slump', 'post-lunch', 'fading fast', 'drowsy',
                             'afternoon energy', 'pick me up', 'picker-upper', 'boost',
                             'yawn', 'dragging', 'back to work', 'the afternoon is',
                             'coffee break']):
        return gen_afternoon(prompt)
    if any(w in p for w in ['4pm', '4 pm', '4:30', '5pm', '5 pm', 'golden hour',
                             'late afternoon', 'sun streaming', 'sun is fading',
                             'end of work', 'autumn afternoon']):
        return gen_late_afternoon(prompt)
    if any(w in p for w in ['sunset', 'dusk', 'twilight', 'sun going down', 'sun set',
                             'sun dip', 'horizon', 'blue hour', 'post-sunset',
                             'getting dark', 'light is changing', 'between afternoon and evening',
                             '6pm', '6 pm', '6 in the evening', '7pm', '7 pm',
                             'evening stroll', 'early evening', 'first light of the evening',
                             'just turned dark']):
        return gen_sunset(prompt)
    if any(w in p for w in ['8pm', '8 pm', '8:30', '8ish', '9pm', '9 pm', '9:30',
                             'evening', 'night is young', 'settling in', 'movie night',
                             'cooking dinner', 'dinner time', 'friday evening',
                             'saturday night']):
        return gen_evening(prompt)
    if any(w in p for w in ['10pm', '10 pm', '10:30', '11pm', '11 pm', '11:30',
                             'getting late', 'bedtime', 'winding down', 'past bedtime',
                             'should go to sleep', 'time for bed', 'nightcap',
                             'wrap up the day', 'high time for bed', 'tomorrow already']):
        return gen_late_evening(prompt)
    if any(w in p for w in ['midnight', 'late night', 'night shift', 'midnight snack',
                             'deep night', 'pitch black', 'streetlights']):
        return gen_night(prompt)

    # --- GENERAL FALLBACKS ---
    if any(w in p for w in ['morning']):
        return gen_morning(prompt)
    if any(w in p for w in ['afternoon']):
        return gen_afternoon(prompt)
    if any(w in p for w in ['evening', 'night']):
        return gen_evening(prompt)
    if any(w in p for w in ['day']):
        return gen_midday(prompt)

    # Ultimate fallback - warm ambient
    return gen_relaxation(prompt)


# ============================================================
# MAIN
# ============================================================

def main():
    input_path = "/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/finetuning/data/remaining_chunk_2.jsonl"
    output_path = "/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/finetuning/data/responses_chunk_2.jsonl"

    # Read all input prompts
    with open(input_path) as f:
        all_prompts = [json.loads(line.strip()) for line in f]

    # Read existing responses
    existing = []
    try:
        with open(output_path) as f:
            existing = [json.loads(line.strip()) for line in f]
    except FileNotFoundError:
        pass

    already_done = len(existing)
    remaining = all_prompts[already_done:]

    print(f"Total prompts: {len(all_prompts)}")
    print(f"Already done: {already_done}")
    print(f"Remaining: {len(remaining)}")

    if not remaining:
        print("All done!")
        return

    # Generate responses
    new_responses = []
    for i, item in enumerate(remaining):
        prompt = item["prompt"]
        response = classify_and_generate(prompt)
        new_responses.append({"prompt": prompt, "response": response})
        if (i + 1) % 50 == 0:
            print(f"  Generated {i+1}/{len(remaining)}")

    # Write all responses (existing + new)
    with open(output_path, 'w') as f:
        for resp in existing:
            f.write(json.dumps(resp) + "\n")
        for resp in new_responses:
            f.write(json.dumps(resp) + "\n")

    total = already_done + len(new_responses)
    print(f"\nDone! Total responses: {total}/{len(all_prompts)}")


if __name__ == "__main__":
    main()

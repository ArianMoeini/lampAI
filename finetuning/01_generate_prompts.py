#!/usr/bin/env python3
"""
Step 1: Generate 2,500+ diverse prompts for the LAMP fine-tuning dataset.

Uses template-based generation with large word banks to create varied,
natural-sounding requests across all lamp capability categories.

Usage:
    python3 01_generate_prompts.py
    python3 01_generate_prompts.py --count 3000
    python3 01_generate_prompts.py --seed 42
"""

import json
import os
import random
import argparse
from itertools import product

# ── Benchmark prompts to EXCLUDE (reserved for evaluation) ──────────────
BENCHMARK_PROMPTS = {
    "show a star", "draw a smiley face", "show an arrow pointing up",
    "draw a house", "show a music note", "draw a cat face", "show a sun",
    "draw a tree", "show a lightning bolt", "draw a skull",
    "show an analog clock at 3 o'clock",
    "be a pomodoro timer", "simulate a sunrise", "create a meditation session",
    "party mode", "simulate rain and thunder",
    "sleep timer that dims over 30 minutes", "countdown from 5",
    "traffic light sequence", "romantic evening ambiance",
    "weather display showing sunny and 24 degrees",
}

# ══════════════════════════════════════════════════════════════════════════
# WORD BANKS
# ══════════════════════════════════════════════════════════════════════════

WARM_COLORS = ["orange", "amber", "warm white", "golden", "peach", "coral",
               "terracotta", "copper", "honey", "sunset orange", "burnt sienna"]
COOL_COLORS = ["blue", "teal", "cyan", "ice blue", "sky blue", "navy",
               "aquamarine", "turquoise", "arctic blue", "steel blue"]
CALM_COLORS = ["lavender", "soft purple", "lilac", "periwinkle", "mauve",
               "dusty rose", "sage green", "seafoam", "powder blue"]
ENERGY_COLORS = ["red", "magenta", "hot pink", "electric blue", "neon green",
                 "bright yellow", "lime", "fuchsia", "vivid orange"]
NATURE_COLORS = ["forest green", "earth brown", "moss green", "leaf green",
                 "olive", "pine", "emerald", "jade", "fern"]
ALL_COLORS = WARM_COLORS + COOL_COLORS + CALM_COLORS + ENERGY_COLORS + NATURE_COLORS

MOODS = ["warm", "cozy", "calm", "relaxing", "energetic", "romantic",
         "mysterious", "spooky", "festive", "professional", "peaceful",
         "moody", "bright", "dark", "soft", "vibrant", "muted", "playful",
         "dramatic", "subtle", "intense", "dreamy", "nostalgic", "futuristic",
         "zen", "melancholy", "cheerful", "elegant", "rustic", "minimalist",
         "luxurious", "whimsical", "serene", "bold", "gentle", "fiery",
         "icy", "tropical", "earthy", "ethereal", "gloomy", "uplifting"]

ACTIVITIES = ["studying", "reading", "meditation", "yoga", "cooking",
              "gaming", "sleeping", "working", "dining", "partying",
              "relaxing", "exercising", "movie watching", "painting",
              "writing", "coding", "napping", "stretching", "journaling",
              "deep work", "brainstorming", "baking", "tea time",
              "wine tasting", "board games", "video call", "podcast listening",
              "homework", "practicing guitar", "doing puzzles"]

TIMES_OF_DAY = ["morning", "afternoon", "evening", "night", "late night",
                "dawn", "dusk", "midnight", "sunrise", "sunset",
                "golden hour", "twilight", "early morning"]

SEASONS = ["spring", "summer", "autumn", "fall", "winter"]

WEATHER = ["rainy day", "sunny day", "snowy evening", "foggy morning",
           "thunderstorm", "cloudy afternoon", "windy night",
           "starry night", "overcast day", "heatwave"]

PLACES = ["beach", "forest", "mountain cabin", "city loft", "garden",
          "library", "coffee shop", "spa", "campfire", "underwater cave",
          "space station", "japanese garden", "northern lights viewing",
          "rooftop terrace", "cozy bedroom", "art studio"]

PIXEL_ART_OBJECTS = [
    "heart", "diamond", "circle", "square", "triangle", "cross",
    "moon", "crescent moon", "cloud", "raindrop", "snowflake",
    "arrow pointing right", "arrow pointing down", "arrow pointing left",
    "smiley", "sad face", "winking face",
    "flower", "tulip", "rose", "sunflower",
    "boat", "car", "rocket", "airplane", "bicycle",
    "fish", "bird", "butterfly", "snake", "rabbit", "dog", "bear",
    "crown", "key", "lock", "flag", "anchor", "umbrella",
    "eye", "hand", "mushroom", "cactus", "mountain",
    "flame", "wave", "sword", "shield", "gem",
    "cup", "bottle", "gift box", "bell", "candle",
    "piano keys", "guitar", "dice", "chess piece", "trophy",
    "clock", "hourglass", "book", "pencil", "lightbulb",
    "planet", "saturn", "alien face", "robot face", "ghost",
    "pumpkin", "christmas tree", "candy cane", "snowman",
    "peace sign", "yin yang", "infinity symbol",
]

PIXEL_ART_VERBS = ["show", "draw", "display", "create", "make",
                   "render", "paint", "pixel art"]

TEXT_WORDS = [
    "HI", "HELLO", "LOVE", "PEACE", "YES", "NO", "OK", "GO",
    "COOL", "WOW", "YAY", "HEY", "BYE", "STOP", "PLAY", "WIN",
    "HOME", "LAMP", "MOON", "STAR", "FIRE", "RAIN", "SUN",
    "A", "B", "C", "X", "Z", "1", "2", "3", "42", "99",
]

NATURAL_PHENOMENA = [
    "sunrise", "sunset", "aurora borealis", "northern lights",
    "ocean waves", "campfire", "volcano eruption", "earthquake",
    "meteor shower", "lightning storm", "tornado", "sandstorm",
    "gentle rain", "heavy rain", "snowfall", "blizzard",
    "solar eclipse", "moonrise", "tidal wave", "fog rolling in",
    "forest fire", "waterfall", "geyser", "lava flow",
]

TIMER_DURATIONS = [
    ("30 seconds", "30s"), ("1 minute", "1min"), ("2 minutes", "2min"),
    ("5 minutes", "5min"), ("10 minutes", "10min"), ("15 minutes", "15min"),
    ("20 minutes", "20min"), ("25 minutes", "25min"), ("30 minutes", "30min"),
    ("45 minutes", "45min"), ("1 hour", "1hr"),
]

COUNTDOWN_NUMBERS = [3, 5, 10, 15, 20, 30, 60]

SPEED_WORDS = ["slow", "fast", "gentle", "rapid", "gradual", "quick",
               "smooth", "pulsing", "flickering", "steady"]

PATTERN_NAMES = ["solid", "gradient", "breathing", "wave", "rainbow",
                 "pulse", "sparkle"]


# ══════════════════════════════════════════════════════════════════════════
# PROMPT GENERATORS (one per category)
# ══════════════════════════════════════════════════════════════════════════

def gen_simple_patterns(rng, count=500):
    """Generate simple single-pattern prompts."""
    prompts = []
    templates = [
        lambda: f"{rng.choice(MOODS)} light",
        lambda: f"{rng.choice(MOODS)} {rng.choice(ALL_COLORS)} light",
        lambda: f"make it {rng.choice(MOODS)}",
        lambda: f"set the color to {rng.choice(ALL_COLORS)}",
        lambda: f"{rng.choice(ALL_COLORS)} {rng.choice(['glow', 'light', 'color', 'hue'])}",
        lambda: f"a {rng.choice(MOODS)} {rng.choice(ALL_COLORS)} {rng.choice(['glow', 'ambiance', 'light', 'atmosphere'])}",
        lambda: f"{rng.choice(SPEED_WORDS)} {rng.choice(ALL_COLORS)} breathing",
        lambda: f"{rng.choice(ALL_COLORS)} and {rng.choice(ALL_COLORS)} gradient",
        lambda: f"{rng.choice(ALL_COLORS)} and {rng.choice(ALL_COLORS)} wave",
        lambda: f"rainbow {rng.choice(['slow', 'fast', 'normal', 'gentle', 'rapid'])}",
        lambda: f"{rng.choice(ALL_COLORS)} sparkle on {rng.choice(['black', 'dark', 'dark blue', 'dark purple'])} background",
        lambda: f"solid {rng.choice(ALL_COLORS)}",
        lambda: f"just {rng.choice(ALL_COLORS)}",
        lambda: f"all {rng.choice(ALL_COLORS)}",
        lambda: f"flash {rng.choice(ALL_COLORS)}",
        lambda: f"{rng.choice(MOODS)} and {rng.choice(MOODS)}",
        lambda: f"something {rng.choice(MOODS)}",
        lambda: f"I want {rng.choice(MOODS)} vibes",
        lambda: f"make it feel {rng.choice(MOODS)}",
        lambda: f"{rng.choice(MOODS)} mood",
        lambda: f"twinkling {rng.choice(ALL_COLORS)} stars",
        lambda: f"pulsing {rng.choice(ALL_COLORS)}",
        lambda: f"gentle {rng.choice(ALL_COLORS)} waves",
        lambda: f"deep {rng.choice(COOL_COLORS + CALM_COLORS)}",
        lambda: f"bright {rng.choice(ENERGY_COLORS + WARM_COLORS)}",
    ]
    while len(prompts) < count:
        t = rng.choice(templates)
        p = t()
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)
    return [{"prompt": p, "category": "pattern"} for p in prompts]


def gen_pixel_art(rng, count=600):
    """Generate pixel art / render prompts."""
    prompts = []
    templates = [
        lambda obj: f"{rng.choice(PIXEL_ART_VERBS)} a {obj}",
        lambda obj: f"{rng.choice(PIXEL_ART_VERBS)} a {rng.choice(ALL_COLORS)} {obj}",
        lambda obj: f"{obj} on the display",
        lambda obj: f"pixel art {obj}",
        lambda obj: f"a small {obj}",
        lambda obj: f"a {rng.choice(MOODS)} {obj}",
        lambda obj: f"{rng.choice(PIXEL_ART_VERBS)} a {rng.choice(['big', 'small', 'tiny', 'cute', 'simple'])} {obj}",
        lambda obj: f"I want to see a {obj}",
        lambda obj: f"can you {rng.choice(['show', 'draw', 'make', 'display'])} a {obj}",
        lambda obj: f"{obj}",
    ]
    while len(prompts) < count:
        obj = rng.choice(PIXEL_ART_OBJECTS)
        t = rng.choice(templates)
        p = t(obj)
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)
    return [{"prompt": p, "category": "render"} for p in prompts]


def gen_multi_step(rng, count=500):
    """Generate multi-step program prompts."""
    prompts = []
    templates = [
        # Timers
        lambda: f"{rng.choice(ACTIVITIES)} timer {rng.choice(TIMER_DURATIONS)[0]}",
        lambda: f"{rng.choice(TIMER_DURATIONS)[0]} {rng.choice(ACTIVITIES)} timer",
        lambda: f"countdown from {rng.choice(COUNTDOWN_NUMBERS)}",
        lambda: f"{rng.choice(ACTIVITIES)} for {rng.choice(TIMER_DURATIONS)[0]} then {rng.choice(ACTIVITIES)} for {rng.choice(TIMER_DURATIONS)[0]}",
        # Simulations
        lambda: f"simulate {rng.choice(NATURAL_PHENOMENA)}",
        lambda: f"simulate a {rng.choice(MOODS)} {rng.choice(NATURAL_PHENOMENA)}",
        lambda: f"{rng.choice(NATURAL_PHENOMENA)} effect",
        lambda: f"show me {rng.choice(NATURAL_PHENOMENA)}",
        # Transitions
        lambda: f"transition from {rng.choice(ALL_COLORS)} to {rng.choice(ALL_COLORS)} over {rng.choice(TIMER_DURATIONS)[0]}",
        lambda: f"fade from {rng.choice(ALL_COLORS)} to {rng.choice(ALL_COLORS)}",
        lambda: f"cycle through {rng.choice(ALL_COLORS)}, {rng.choice(ALL_COLORS)}, and {rng.choice(ALL_COLORS)}",
        lambda: f"alternate between {rng.choice(ALL_COLORS)} and {rng.choice(ALL_COLORS)}",
        # Pomodoro variants
        lambda: f"pomodoro {rng.choice(TIMER_DURATIONS)[0]} work {rng.choice(TIMER_DURATIONS)[0]} break",
        lambda: f"focus timer with {rng.choice(TIMER_DURATIONS)[0]} work and {rng.choice(TIMER_DURATIONS)[0]} rest",
        # Activity sequences
        lambda: f"morning routine light sequence",
        lambda: f"bedtime routine over {rng.choice(['15 minutes', '20 minutes', '30 minutes', '1 hour'])}",
        lambda: f"wake up light that starts dim and gets bright over {rng.choice(TIMER_DURATIONS)[0]}",
        lambda: f"sleep timer that dims over {rng.choice(['15 minutes', '20 minutes', '30 minutes', '45 minutes'])}",
        lambda: f"{rng.choice(MOODS)} {rng.choice(['sequence', 'animation', 'light show', 'display'])}",
        # Event-based
        lambda: f"{rng.choice(['birthday', 'new year', 'halloween', 'christmas', 'valentines', 'celebration', 'game day', 'movie night'])} {rng.choice(['mode', 'light show', 'theme', 'animation'])}",
        lambda: f"traffic light {rng.choice(['sequence', 'pattern', 'cycle'])}",
        lambda: f"disco {rng.choice(['mode', 'lights', 'party'])}",
        lambda: f"{rng.choice(['police', 'ambulance', 'fire truck', 'emergency'])} lights",
        lambda: f"breathing exercise {rng.choice(['4-7-8', '4 seconds in 4 seconds out', 'box breathing', 'calm breathing'])}",
    ]
    while len(prompts) < count:
        t = rng.choice(templates)
        p = t()
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)
    return [{"prompt": p, "category": "multi_step"} for p in prompts]


def gen_mixed(rng, count=200):
    """Generate prompts that combine render + pattern in multi-step programs."""
    prompts = []
    templates = [
        lambda: f"show a {rng.choice(PIXEL_ART_OBJECTS)} then fade to {rng.choice(ALL_COLORS)}",
        lambda: f"display {rng.choice(TEXT_WORDS)} then rainbow",
        lambda: f"countdown from {rng.choice([3, 5, 10])} then {rng.choice(['celebrate', 'party mode', 'rainbow', 'flash green'])}",
        lambda: f"show a {rng.choice(PIXEL_ART_OBJECTS)} with {rng.choice(MOODS)} background animation",
        lambda: f"draw a {rng.choice(PIXEL_ART_OBJECTS)} for {rng.choice(TIMER_DURATIONS)[0]} then breathing {rng.choice(ALL_COLORS)}",
        lambda: f"show {rng.choice(TEXT_WORDS)} then sparkle for {rng.choice(TIMER_DURATIONS)[0]}",
        lambda: f"flash {rng.choice(ALL_COLORS)} then show a {rng.choice(PIXEL_ART_OBJECTS)}",
        lambda: f"show a {rng.choice(PIXEL_ART_OBJECTS)} that {rng.choice(['pulses', 'breathes', 'sparkles', 'glows'])}",
    ]
    while len(prompts) < count:
        t = rng.choice(templates)
        p = t()
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)
    return [{"prompt": p, "category": "mixed"} for p in prompts]


def gen_text_display(rng, count=200):
    """Generate text display / clock prompts."""
    prompts = []
    templates = [
        lambda: f"display {rng.choice(TEXT_WORDS)}",
        lambda: f"show the text {rng.choice(TEXT_WORDS)}",
        lambda: f"write {rng.choice(TEXT_WORDS)} in {rng.choice(ALL_COLORS)}",
        lambda: f"show {rng.choice(TEXT_WORDS)} on {rng.choice(['black', 'dark blue', 'dark purple', 'dark green'])} background",
        lambda: f"clock showing {rng.randint(1, 12)}:{rng.choice(['00', '15', '30', '45'])}",
        lambda: f"show the time {rng.randint(0, 23)}:{rng.choice(['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'])}",
        lambda: f"display temperature {rng.randint(-10, 40)} degrees",
        lambda: f"show score {rng.randint(0, 9)}-{rng.randint(0, 9)}",
        lambda: f"display the number {rng.randint(0, 99)}",
        lambda: f"show {rng.choice(TEXT_WORDS)} in {rng.choice(ALL_COLORS)} on {rng.choice(['dark', 'black'])} background",
    ]
    while len(prompts) < count:
        t = rng.choice(templates)
        p = t()
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)
    return [{"prompt": p, "category": "text"} for p in prompts]


def gen_creative(rng, count=300):
    """Generate creative / ambiguous / mood-based prompts."""
    prompts = []
    templates = [
        lambda: f"set the mood for {rng.choice(ACTIVITIES)}",
        lambda: f"perfect light for a {rng.choice(WEATHER)}",
        lambda: f"make it feel like {rng.choice(SEASONS)}",
        lambda: f"I'm feeling {rng.choice(MOODS)}, match my mood",
        lambda: f"like being at a {rng.choice(PLACES)}",
        lambda: f"imagine a {rng.choice(PLACES)} at {rng.choice(TIMES_OF_DAY)}",
        lambda: f"{rng.choice(MOODS)} {rng.choice(TIMES_OF_DAY)} light",
        lambda: f"lights for {rng.choice(TIMES_OF_DAY)}",
        lambda: f"something for a {rng.choice(MOODS)} {rng.choice(TIMES_OF_DAY)}",
        lambda: f"make the room feel like {rng.choice(PLACES)}",
        lambda: f"date night",
        lambda: f"surprise me",
        lambda: f"something different",
        lambda: f"make it interesting",
        lambda: f"whatever feels right",
        lambda: f"something beautiful",
        lambda: f"chill vibes",
        lambda: f"{rng.choice(SEASONS)} {rng.choice(TIMES_OF_DAY)} vibes",
        lambda: f"like a {rng.choice(['90s rave', 'jazz club', 'sunset beach', 'haunted house', 'fairy tale', 'cyberpunk city', 'underwater world', 'outer space', 'enchanted forest', 'desert oasis'])}",
        lambda: f"{rng.choice(MOODS)} atmosphere for {rng.choice(ACTIVITIES)}",
        lambda: f"the perfect {rng.choice(TIMES_OF_DAY)} ambiance",
        lambda: f"match the vibe of a {rng.choice(PLACES)}",
    ]
    while len(prompts) < count:
        t = rng.choice(templates)
        p = t()
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)
    return [{"prompt": p, "category": "creative"} for p in prompts]


def gen_edge_cases(rng, count=200):
    """Generate edge case prompts (very short, very long, unusual)."""
    prompts = []

    # Very short (single word)
    short = [c for c in ALL_COLORS] + list(MOODS)[:20] + ["stop", "off", "on", "help", "reset", "party", "chill", "sleep", "wake", "focus", "relax", "fire"]
    for s in rng.sample(short, min(50, len(short))):
        prompts.append(s)

    # Very long / conversational
    long_templates = [
        lambda: f"I would really love it if you could make the lamp feel like a {rng.choice(MOODS)} {rng.choice(PLACES)} during {rng.choice(TIMES_OF_DAY)} with {rng.choice(ALL_COLORS)} tones",
        lambda: f"can you please create something that feels like sitting by a fireplace in a cozy cabin during a {rng.choice(SEASONS)} {rng.choice(WEATHER)} while {rng.choice(ACTIVITIES)}",
        lambda: f"make it look like the sky during a {rng.choice(MOODS)} {rng.choice(NATURAL_PHENOMENA)} with lots of {rng.choice(ALL_COLORS)} and {rng.choice(ALL_COLORS)} colors",
        lambda: f"I want something that starts {rng.choice(MOODS)} and slowly becomes {rng.choice(MOODS)} over the course of the {rng.choice(TIMES_OF_DAY)}",
        lambda: f"set it to a nice {rng.choice(ALL_COLORS)} and {rng.choice(ALL_COLORS)} combination that would be great for {rng.choice(ACTIVITIES)} during the {rng.choice(TIMES_OF_DAY)}",
    ]
    while len(prompts) < count - 30:
        t = rng.choice(long_templates)
        p = t()
        if p not in BENCHMARK_PROMPTS and p not in prompts:
            prompts.append(p)

    # Typos / informal
    informal = [
        "somthing warm", "blu light", "mak it cozy", "red pls",
        "idk something nice", "just do something cool", "green-ish",
        "warm but not too warm", "like sunset but more purple",
        "bright but chill", "dark but not scary",
        "can u make it romantic", "yo party time", "chill mode plz",
        "gimme something spooky", "vibes", "mood lighting",
        "aesthetic af", "lo-fi vibes", "cottagecore",
        "dark academia", "vaporwave", "cyberpunk",
        "synthwave", "retro", "neon", "pastel",
        "earth tones", "monochrome", "all white",
        "pitch black", "dim everything",
    ]
    for s in informal:
        if s not in prompts and len(prompts) < count:
            prompts.append(s)

    return [{"prompt": p, "category": "edge_case"} for p in prompts[:count]]


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate diverse lamp prompts")
    parser.add_argument("--count", type=int, default=2500, help="Target total prompts")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # Scale category counts proportionally to target
    scale = args.count / 2500
    categories = [
        ("pattern",    gen_simple_patterns, int(500 * scale)),
        ("render",     gen_pixel_art,       int(600 * scale)),
        ("multi_step", gen_multi_step,      int(500 * scale)),
        ("mixed",      gen_mixed,           int(200 * scale)),
        ("text",       gen_text_display,    int(200 * scale)),
        ("creative",   gen_creative,        int(300 * scale)),
        ("edge_case",  gen_edge_cases,      int(200 * scale)),
    ]

    all_prompts = []
    for name, gen_fn, count in categories:
        items = gen_fn(rng, count)
        all_prompts.extend(items)
        print(f"  {name:12s}: {len(items):4d} prompts")

    # Deduplicate
    seen = set()
    unique = []
    for item in all_prompts:
        key = item["prompt"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Shuffle
    rng.shuffle(unique)

    # Save
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "prompts.jsonl")

    with open(out_path, "w") as f:
        for item in unique:
            f.write(json.dumps(item) + "\n")

    print(f"\n  Total unique prompts: {len(unique)}")
    print(f"  Saved to: {out_path}")

    # Category breakdown
    cats = {}
    for item in unique:
        cats[item["category"]] = cats.get(item["category"], 0) + 1
    print("\n  Category distribution:")
    for cat, cnt in sorted(cats.items()):
        print(f"    {cat:12s}: {cnt:4d} ({cnt/len(unique)*100:.1f}%)")


if __name__ == "__main__":
    main()

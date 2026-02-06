#!/usr/bin/env python3
"""
Step 2: Generate Opus-quality JSON lamp program responses for every prompt.

This script contains handcrafted pixel art definitions, mood-to-color mapping,
pattern selection logic, and multi-step program composition to generate
high-quality training data without needing API calls.

Usage:
    python3 02_generate_responses.py
    python3 02_generate_responses.py --seed 42
"""

import json
import os
import re
import random
import argparse

# ══════════════════════════════════════════════════════════════════════════
# PIXEL ART LIBRARY — handcrafted coordinate definitions for 10×14 grid
# Each shape is a list of {"type": ..., ...} render elements.
# Grid: x=0..9 (left to right), y=0..13 (top to bottom)
# ══════════════════════════════════════════════════════════════════════════

def _px(coords, color):
    """Helper: convert list of (x,y) to pixel elements."""
    return [{"type": "pixel", "x": x, "y": y, "color": color} for x, y in coords]

def _rect(x, y, w, h, color):
    return {"type": "rect", "x": x, "y": y, "w": w, "h": h, "color": color}

def _fill(color):
    return {"type": "fill", "color": color}

def _text(content, x, y, color):
    return {"type": "text", "content": content, "x": x, "y": y, "color": color}

def _line(x1, y1, x2, y2, color):
    return {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color}


# All pixel art shapes: returns (elements_list, suggested_fg_color, suggested_bg_color)
PIXEL_ART_DEFS = {}

def _register(name, elements_fn):
    PIXEL_ART_DEFS[name] = elements_fn

# ── Basic shapes ─────────────────────────────────────────────────────────

_register("heart", lambda fg="#FF2266", bg="#1a0a1a": [
    _fill(bg),
    *_px([(3,3),(4,3),(6,3),(7,3),
          (2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),
          (2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7),
          (5,8)], fg)
])

_register("diamond", lambda fg="#00BFFF", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,2),
          (4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7),
          (5,8)], fg)
])

_register("circle", lambda fg="#44AAFF", bg="#0a0a1a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(7,3),
          (2,4),(8,4),
          (2,5),(8,5),
          (2,6),(8,6),
          (3,7),(7,7),
          (4,8),(5,8),(6,8)], fg)
])

_register("square", lambda fg="#FFD700", bg="#0a0a2a": [
    _fill(bg),
    _rect(2, 3, 7, 1, fg), _rect(2, 9, 7, 1, fg),
    *_px([(2,4),(2,5),(2,6),(2,7),(2,8),
          (8,4),(8,5),(8,6),(8,7),(8,8)], fg)
])

_register("triangle", lambda fg="#FF6B4A", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,2),
          (4,3),(5,3),(6,3),
          (3,4),(6,4),
          (2,5),(7,5),
          (1,6),(8,6)], fg),
    _rect(1, 7, 8, 1, fg)
])

_register("cross", lambda fg="#FF4444", bg="#0a0a1a": [
    _fill(bg),
    _rect(4, 1, 2, 10, fg),
    _rect(1, 4, 8, 2, fg),
])

# ── Celestial ────────────────────────────────────────────────────────────

_register("moon", lambda fg="#FFFFCC", bg="#0a0a2a": [
    _fill(bg),
    *_px([(6,1),(7,1),
          (5,2),(8,2),
          (4,3),(8,3),
          (4,4),(7,4),
          (4,5),(7,5),
          (4,6),(8,6),
          (5,7),(8,7),
          (6,8),(7,8)], fg)
])

_register("crescent moon", lambda fg="#FFFFAA", bg="#0a0a2a": [
    _fill(bg),
    *_px([(6,1),(7,1),
          (5,2),
          (4,3),
          (4,4),
          (4,5),
          (5,6),
          (6,7),(7,7)], fg),
    *_px([(3,3),(3,4),(3,5),(4,6),(5,7)], "#8888AA")  # dim inner edge
])

_register("cloud", lambda fg="#FFFFFF", bg="#87CEEB": [
    _fill(bg),
    *_px([(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),
          (2,6),(3,6),(4,6),(5,6),(6,6),(7,6),(8,6)], fg)
])

_register("raindrop", lambda fg="#4488FF", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1),
          (4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5),
          (5,6)], fg)
])

_register("snowflake", lambda fg="#CCDDFF", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1),(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8),(5,9),  # vertical
          (1,5),(2,5),(3,5),(4,5),(6,5),(7,5),(8,5),(9,5),  # horizontal
          (3,3),(7,3),(3,7),(7,7),  # diagonals
          (2,2),(8,2),(2,8),(8,8)], fg)
])

# ── Arrows ───────────────────────────────────────────────────────────────

_register("arrow pointing right", lambda fg="#00FF88", bg="#0a0a1a": [
    _fill(bg),
    _rect(1, 5, 6, 2, fg),
    *_px([(7,4),(7,5),(7,6),(7,7),
          (8,5),(8,6),
          (9,5)], fg),
    *_px([(6,3),(7,3),(6,8),(7,8)], fg)
])

_register("arrow pointing down", lambda fg="#FF6B4A", bg="#0a0a1a": [
    _fill(bg),
    _rect(4, 1, 2, 7, fg),
    *_px([(3,8),(4,8),(5,8),(6,8),
          (2,7),(7,7),
          (3,9),(6,9),
          (4,10),(5,10)], fg)
])

_register("arrow pointing left", lambda fg="#44AAFF", bg="#0a0a1a": [
    _fill(bg),
    _rect(3, 5, 6, 2, fg),
    *_px([(2,4),(2,5),(2,6),(2,7),
          (1,5),(1,6),
          (0,5)], fg),
    *_px([(3,3),(2,3),(3,8),(2,8)], fg)
])

# ── Nature ───────────────────────────────────────────────────────────────

_register("flower", lambda fg="#FF69B4", bg="#0a1a0a": [
    _fill(bg),
    *_px([(5,2),(4,3),(6,3),(3,4),(7,4),(4,5),(6,5),(5,6)], fg),  # petals
    *_px([(5,3),(5,4),(5,5)], "#FFD700"),  # center
    *_px([(5,7),(5,8),(5,9),(5,10)], "#228B22"),  # stem
    *_px([(4,9),(6,8)], "#228B22"),  # leaves
])

_register("tulip", lambda fg="#FF4466", bg="#0a1a0a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (4,4),(5,4),(6,4)], fg),
    *_px([(5,5),(5,6),(5,7),(5,8),(5,9),(5,10)], "#228B22"),
    *_px([(4,7),(3,8),(6,7),(7,8)], "#228B22"),
])

_register("rose", lambda fg="#CC0033", bg="#0a0a0a": [
    _fill(bg),
    *_px([(5,2),(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5)], fg),
    *_px([(5,6),(5,7),(5,8),(5,9),(5,10)], "#2D5A27"),
    *_px([(4,8),(3,9),(6,7),(7,6)], "#2D5A27"),
])

_register("sunflower", lambda fg="#FFD700", bg="#87CEEB": [
    _fill(bg),
    *_px([(5,1),(3,2),(7,2),(2,3),(8,3),(2,5),(8,5),(3,6),(7,6),(5,7)], fg),  # petals
    *_px([(4,3),(5,3),(6,3),(4,4),(5,4),(6,4),(4,5),(5,5),(6,5)], "#8B4513"),  # center
    *_px([(5,8),(5,9),(5,10),(5,11)], "#228B22"),
])

_register("mushroom", lambda fg="#FF4444", bg="#0a1a0a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4)], fg),
    *_px([(4,3),(6,3),(3,4),(5,4),(7,4)], "#FFFFFF"),  # spots
    *_px([(4,5),(5,5),(6,5),(4,6),(5,6),(6,6),
          (5,7),(5,8),(5,9)], "#DEB887"),  # stem
])

_register("cactus", lambda fg="#228B22", bg="#DEB887": [
    _fill(bg),
    *_px([(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8),(5,9),(5,10)], fg),
    *_px([(4,3),(4,4),(4,5)], fg),
    *_px([(3,5)], fg),
    *_px([(6,5),(6,6),(6,7)], fg),
    *_px([(7,5)], fg),
])

_register("mountain", lambda fg="#666666", bg="#87CEEB": [
    _fill(bg),
    *_px([(5,3),(4,4),(5,4),(6,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (2,6),(3,6),(4,6),(5,6),(6,6),(7,6),(8,6)], fg),
    _rect(1, 7, 9, 3, fg),
    *_px([(5,3),(4,4),(5,4),(6,4)], "#FFFFFF"),  # snow cap
])

# ── Animals ──────────────────────────────────────────────────────────────

_register("fish", lambda fg="#FF8C00", bg="#003366": [
    _fill(bg),
    *_px([(4,4),(5,4),(6,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (4,6),(5,6),(6,6),
          (2,4),(2,6),(1,3),(1,7)], fg),
    *_px([(6,5)], "#000000"),  # eye
])

_register("bird", lambda fg="#FF6347", bg="#87CEEB": [
    _fill(bg),
    *_px([(6,3),(7,3),
          (4,4),(5,4),(6,4),(7,4),(8,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (4,6),(5,6),(6,6)], fg),
    *_px([(7,4)], "#000000"),  # eye
    *_px([(9,4),(9,5)], "#FFD700"),  # beak
])

_register("butterfly", lambda fg="#FF69B4", bg="#0a1a0a": [
    _fill(bg),
    *_px([(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8)], "#8B4513"),  # body
    *_px([(3,3),(4,3),(2,4),(3,4),(4,4),(2,5),(3,5),(4,5),(3,6),(4,6)], fg),  # left wing
    *_px([(6,3),(7,3),(6,4),(7,4),(8,4),(6,5),(7,5),(8,5),(6,6),(7,6)], "#9370DB"),  # right wing
])

_register("snake", lambda fg="#228B22", bg="#DEB887": [
    _fill(bg),
    *_px([(2,3),(3,3),(4,3),(5,3),
          (5,4),(5,5),
          (4,5),(3,5),(2,5),
          (2,6),(2,7),
          (3,7),(4,7),(5,7),(6,7),
          (6,8)], fg),
    *_px([(2,3)], "#FF0000"),  # tongue
])

_register("rabbit", lambda fg="#FFFFFF", bg="#228B22": [
    _fill(bg),
    *_px([(4,1),(4,2),(4,3),(6,1),(6,2),(6,3)], fg),  # ears
    *_px([(4,4),(5,4),(6,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (4,6),(5,6),(6,6)], fg),  # head
    *_px([(4,5),(6,5)], "#FF0000"),  # eyes
    *_px([(5,6)], "#FFB6C1"),  # nose
    *_px([(4,7),(5,7),(6,7),(4,8),(5,8),(6,8)], fg),  # body
])

_register("dog", lambda fg="#C4A882", bg="#0a1a1a": [
    _fill(bg),
    *_px([(3,2),(3,3),(7,2),(7,3)], fg),  # ears
    *_px([(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5)], fg),  # head
    *_px([(4,4),(6,4)], "#000000"),  # eyes
    *_px([(5,5)], "#000000"),  # nose
    *_px([(4,6),(5,6),(6,6),(4,7),(5,7),(6,7),(4,8),(5,8),(6,8)], fg),  # body
    *_px([(3,9),(7,9)], fg),  # legs
])

_register("bear", lambda fg="#8B4513", bg="#0a1a0a": [
    _fill(bg),
    *_px([(3,2),(7,2)], fg),  # ears
    *_px([(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5)], fg),
    *_px([(4,4),(6,4)], "#000000"),
    *_px([(5,5)], "#000000"),
    *_px([(3,6),(4,6),(5,6),(6,6),(7,6),
          (3,7),(4,7),(5,7),(6,7),(7,7),
          (3,8),(4,8),(6,8),(7,8)], fg),
])

_register("ghost", lambda fg="#FFFFFF", bg="#1a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (3,7),(4,7),(5,7),(6,7),(7,7),
          (3,8),(5,8),(7,8)], fg),
    *_px([(4,4),(6,4)], "#000000"),  # eyes
    *_px([(5,5)], "#000000"),  # mouth
])

# ── Objects ──────────────────────────────────────────────────────────────

_register("crown", lambda fg="#FFD700", bg="#1a0a2a": [
    _fill(bg),
    *_px([(2,4),(5,4),(8,4),
          (2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),
          (3,6),(4,6),(5,6),(6,6),(7,6)], fg),
    *_px([(3,5),(5,5),(7,5)], "#FF0000"),  # gems
    _rect(2, 7, 7, 1, fg),
])

_register("key", lambda fg="#FFD700", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),(4,3),(6,3),(4,4),(5,4),(6,4)], fg),  # head
    *_px([(5,5),(5,6),(5,7),(5,8),(5,9)], fg),  # shaft
    *_px([(6,8),(7,8),(6,9)], fg),  # teeth
])

_register("lock", lambda fg="#888888", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),(3,3),(7,3),(3,4),(7,4)], fg),  # shackle
    _rect(2, 5, 7, 5, fg),  # body
    *_px([(5,7),(5,8)], "#FFD700"),  # keyhole
])

_register("flag", lambda fg="#FF0000", bg="#87CEEB": [
    _fill(bg),
    *_px([(2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10)], "#666666"),  # pole
    _rect(3, 2, 5, 4, fg),  # flag
])

_register("anchor", lambda fg="#4A6FA5", bg="#003366": [
    _fill(bg),
    *_px([(5,1),(4,2),(5,2),(6,2)], fg),  # top
    *_px([(5,3),(5,4),(5,5),(5,6),(5,7),(5,8)], fg),  # shaft
    *_px([(3,7),(2,8),(8,7),(7,8)], fg),  # flukes
    _rect(2, 9, 7, 1, fg),  # bottom
])

_register("umbrella", lambda fg="#FF4444", bg="#87CEEB": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4)], fg),
    *_px([(5,5),(5,6),(5,7),(5,8),(5,9)], "#8B4513"),  # handle
    *_px([(4,9),(3,9)], "#8B4513"),  # hook
])

_register("cup", lambda fg="#DEB887", bg="#0a0a1a": [
    _fill(bg),
    _rect(3, 3, 5, 6, fg),
    *_px([(8,4),(8,5),(8,6),(7,6)], fg),  # handle
    *_px([(4,4),(5,4),(6,4)], "#6B3A2A"),  # coffee
])

_register("bottle", lambda fg="#228B22", bg="#0a0a1a": [
    _fill(bg),
    *_px([(5,1),(5,2)], fg),  # cap
    *_px([(4,3),(5,3),(6,3)], fg),  # neck
    _rect(3, 4, 5, 7, fg),  # body
])

_register("gift box", lambda fg="#FF4444", bg="#0a1a0a": [
    _fill(bg),
    _rect(2, 4, 7, 5, fg),  # box
    _rect(5, 4, 1, 5, "#FFD700"),  # ribbon vertical
    _rect(2, 3, 7, 1, "#FFD700"),  # ribbon horizontal / lid
    *_px([(4,2),(6,2)], "#FFD700"),  # bow
])

_register("bell", lambda fg="#FFD700", bg="#0a1a0a": [
    _fill(bg),
    *_px([(5,1)], fg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),
          (2,6),(3,6),(4,6),(5,6),(6,6),(7,6),(8,6)], fg),
    *_px([(5,7)], "#CC0000"),  # clapper
])

_register("candle", lambda fg="#FFFFCC", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1),(4,2),(5,2),(6,2)], "#FF6600"),  # flame
    *_px([(5,3)], "#FFD700"),  # wick
    _rect(4, 4, 3, 6, fg),  # wax
])

_register("trophy", lambda fg="#FFD700", bg="#0a0a2a": [
    _fill(bg),
    *_px([(3,2),(4,2),(5,2),(6,2),(7,2)], fg),  # top rim
    *_px([(3,3),(4,3),(5,3),(6,3),(7,3),
          (4,4),(5,4),(6,4),
          (5,5)], fg),  # cup
    *_px([(2,3),(8,3)], fg),  # handles
    *_px([(5,6),(5,7)], fg),  # stem
    _rect(3, 8, 5, 1, fg),  # base
])

_register("hourglass", lambda fg="#DEB887", bg="#0a0a2a": [
    _fill(bg),
    _rect(2, 2, 7, 1, "#888888"),
    *_px([(3,3),(4,3),(5,3),(6,3),(7,3),
          (4,4),(5,4),(6,4),
          (5,5),
          (4,6),(5,6),(6,6),
          (3,7),(4,7),(5,7),(6,7),(7,7)], fg),
    _rect(2, 8, 7, 1, "#888888"),
])

_register("book", lambda fg="#8B4513", bg="#0a0a2a": [
    _fill(bg),
    _rect(2, 3, 7, 7, fg),
    *_px([(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9)], "#FFFFFF"),  # pages
    _rect(3, 4, 5, 1, "#FFD700"),  # title line
])

_register("pencil", lambda fg="#FFD700", bg="#0a0a1a": [
    _fill(bg),
    *_px([(5,1)], "#333333"),  # tip
    *_px([(5,2),(5,3)], "#DEB887"),  # wood
    _rect(4, 4, 3, 5, fg),  # body
    *_px([(4,9),(5,9),(6,9)], "#FF69B4"),  # eraser
])

_register("lightbulb", lambda fg="#FFFF44", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5)], fg),
    *_px([(4,6),(5,6),(6,6)], "#888888"),  # base
    *_px([(4,7),(5,7),(6,7)], "#888888"),
])

# ── Space ────────────────────────────────────────────────────────────────

_register("planet", lambda fg="#4488CC", bg="#0a0a1a": [
    _fill(bg),
    *_px([(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7)], fg),
    *_px([(2,5),(1,5),(8,5),(9,5)], "#886644"),  # ring
])

_register("saturn", lambda fg="#DAA520", bg="#0a0a1a": [
    _fill(bg),
    *_px([(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (4,6),(5,6),(6,6)], fg),
    *_px([(1,4),(2,4),(8,4),(9,4),(0,5),(1,5),(8,5),(9,5)], "#B8860B"),  # ring
])

_register("alien face", lambda fg="#44FF44", bg="#0a0a1a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5),
          (5,6)], fg),
    *_px([(3,4),(4,4)], "#000000"),  # left eye
    *_px([(6,4),(7,4)], "#000000"),  # right eye
    *_px([(5,5)], "#000000"),  # mouth
])

_register("robot face", lambda fg="#AAAAAA", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1)], "#FF0000"),  # antenna
    _rect(3, 2, 5, 6, fg),
    *_px([(4,3),(4,4)], "#00FFFF"),  # left eye
    *_px([(6,3),(6,4)], "#00FFFF"),  # right eye
    _rect(4, 6, 3, 1, "#FF0000"),  # mouth
])

# ── Seasonal ─────────────────────────────────────────────────────────────

_register("pumpkin", lambda fg="#FF6600", bg="#1a0a2a": [
    _fill(bg),
    *_px([(5,1),(5,2)], "#228B22"),  # stem
    *_px([(4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7)], fg),
    *_px([(4,4),(6,4)], "#000000"),  # eyes
    *_px([(4,6),(5,6),(6,6)], "#000000"),  # mouth
])

_register("christmas tree", lambda fg="#228B22", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1)], "#FFD700"),  # star
    *_px([(5,2),
          (4,3),(5,3),(6,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (4,5),(5,5),(6,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (2,7),(3,7),(4,7),(5,7),(6,7),(7,7),(8,7)], fg),
    *_px([(5,8),(5,9)], "#8B4513"),  # trunk
    *_px([(4,4),(6,6),(3,7)], "#FF0000"),  # ornaments
    *_px([(6,3),(4,6),(7,7)], "#FFD700"),
])

_register("candy cane", lambda fg="#FF0000", bg="#0a1a0a": [
    _fill(bg),
    *_px([(5,1),(6,1),(7,1),(7,2)], fg),
    *_px([(6,1)], "#FFFFFF"),
    *_px([(6,2),(6,3),(6,4),(6,5),(6,6),(6,7),(6,8),(6,9)], fg),
    *_px([(6,3),(6,5),(6,7),(6,9)], "#FFFFFF"),
])

_register("snowman", lambda fg="#FFFFFF", bg="#87CEEB": [
    _fill(bg),
    *_px([(5,1)], "#000000"),  # hat top
    _rect(4, 2, 3, 1, "#000000"),  # hat brim
    *_px([(4,3),(5,3),(6,3)], fg),  # head
    *_px([(4,3),(6,3)], "#000000"),  # eyes
    *_px([(5,4)], "#FF6600"),  # nose
    *_px([(3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6)], fg),  # body
    *_px([(4,8),(5,8),(6,8),
          (3,9),(4,9),(5,9),(6,9),(7,9)], fg),  # base
])

# ── Symbols ──────────────────────────────────────────────────────────────

_register("peace sign", lambda fg="#FFFFFF", bg="#1a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(7,3),
          (2,4),(5,4),(8,4),
          (2,5),(5,5),(8,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7),
          (4,8),(5,8),(6,8)], fg)
])

_register("yin yang", lambda fg="#FFFFFF", bg="#0a0a0a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(7,3),
          (2,4),(3,4),(4,4),(8,4),
          (2,5),(3,5),(8,5),
          (3,6),(7,6),(8,6),
          (4,7),(5,7),(6,7),(7,7),
          (5,8),(6,8)], fg),
    *_px([(5,3)], "#000000"),  # dark dot in white
    *_px([(5,7)], "#FFFFFF"),  # white dot in dark (already white)
])

_register("infinity symbol", lambda fg="#9370DB", bg="#0a0a1a": [
    _fill(bg),
    *_px([(2,4),(3,3),(4,4),(5,5),(6,4),(7,3),(8,4),
          (2,6),(3,7),(4,6),(5,5),(6,6),(7,7),(8,6),
          (1,5),(9,5)], fg)
])

# ── Vehicles ─────────────────────────────────────────────────────────────

_register("boat", lambda fg="#8B4513", bg="#003366": [
    _fill(bg),
    *_px([(5,2),(5,3),(5,4)], "#FFFFFF"),  # mast
    *_px([(6,3),(7,3),(6,4),(7,4),(8,4)], "#FFFFFF"),  # sail
    _rect(2, 5, 7, 2, fg),  # hull
    *_px([(1,6),(9,6)], fg),  # edges
    *_px([(2,7),(3,7),(4,7),(5,7),(6,7),(7,7),(8,7)], "#1a3366"),  # water
])

_register("car", lambda fg="#FF4444", bg="#87CEEB": [
    _fill(bg),
    *_px([(4,4),(5,4),(6,4)], fg),  # roof
    _rect(2, 5, 7, 2, fg),  # body
    *_px([(3,5),(4,5),(6,5),(7,5)], "#88CCFF"),  # windows
    *_px([(3,7),(7,7)], "#333333"),  # wheels
    _rect(1, 8, 9, 2, "#666666"),  # road
])

_register("rocket", lambda fg="#CCCCCC", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1),(4,2),(5,2),(6,2)], "#FF4444"),  # nose
    _rect(4, 3, 3, 5, fg),  # body
    *_px([(3,6),(3,7),(7,6),(7,7)], "#4444FF"),  # fins
    *_px([(4,8),(5,8),(6,8)], "#FF6600"),  # flame
    *_px([(5,9)], "#FFFF00"),
])

_register("airplane", lambda fg="#FFFFFF", bg="#87CEEB": [
    _fill(bg),
    *_px([(5,2),(5,3),(5,4),(5,5),(5,6),(5,7)], fg),  # body
    *_px([(2,4),(3,4),(4,4),(6,4),(7,4),(8,4)], fg),  # wings
    *_px([(4,7),(6,7)], fg),  # tail
])

_register("bicycle", lambda fg="#333333", bg="#87CEEB": [
    _fill(bg),
    # wheels
    *_px([(2,6),(1,7),(3,7),(2,8)], fg),
    *_px([(7,6),(6,7),(8,7),(7,8)], fg),
    # frame
    *_px([(3,5),(4,5),(5,5),(6,5),(5,4),(4,4)], fg),
    *_px([(5,3)], fg),  # seat
    *_px([(7,4)], fg),  # handlebar
])

# ── Misc ─────────────────────────────────────────────────────────────────

_register("flame", lambda fg="#FF4400", bg="#0a0a0a": [
    _fill(bg),
    *_px([(5,2)], "#FFFF00"),
    *_px([(4,3),(5,3),(6,3)], "#FFDD00"),
    *_px([(4,4),(5,4),(6,4)], "#FFAA00"),
    *_px([(3,5),(4,5),(5,5),(6,5),(7,5)], fg),
    *_px([(3,6),(4,6),(5,6),(6,6),(7,6)], fg),
    *_px([(4,7),(5,7),(6,7)], "#CC2200"),
    *_px([(4,8),(5,8),(6,8)], "#881100"),
])

_register("wave", lambda fg="#4488FF", bg="#003366": [
    _fill(bg),
    *_px([(1,4),(2,3),(3,4),(4,5),(5,4),(6,3),(7,4),(8,5),(9,4)], fg),
    *_px([(0,5),(1,5),(2,4),(3,5),(4,6),(5,5),(6,4),(7,5),(8,6),(9,5)], "#2266CC"),
])

_register("sword", lambda fg="#CCCCCC", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1),(5,2),(5,3),(5,4),(5,5)], fg),  # blade
    *_px([(3,6),(4,6),(5,6),(6,6),(7,6)], "#8B4513"),  # guard
    *_px([(5,7),(5,8)], "#8B4513"),  # hilt
    *_px([(5,9)], "#FFD700"),  # pommel
])

_register("shield", lambda fg="#4444CC", bg="#0a0a2a": [
    _fill(bg),
    *_px([(3,2),(4,2),(5,2),(6,2),(7,2),
          (2,3),(3,3),(4,3),(5,3),(6,3),(7,3),(8,3),
          (2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (4,6),(5,6),(6,6),
          (5,7)], fg),
    *_px([(5,3),(5,4),(5,5),(4,4),(6,4)], "#FFD700"),  # emblem
])

_register("gem", lambda fg="#FF00FF", bg="#0a0a2a": [
    _fill(bg),
    _rect(3, 3, 5, 1, fg),
    *_px([(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4)], fg),
    *_px([(3,5),(4,5),(5,5),(6,5),(7,5)], "#CC00CC"),
    *_px([(4,6),(5,6),(6,6)], "#AA00AA"),
    *_px([(5,7)], "#880088"),
])

_register("dice", lambda fg="#FFFFFF", bg="#0a0a2a": [
    _fill(bg),
    _rect(2, 3, 7, 7, fg),
    *_px([(4,5),(6,5),(4,7),(6,7),(5,6)], "#000000"),  # five dots
])

_register("chess piece", lambda fg="#FFFFFF", bg="#228B22": [
    _fill(bg),
    *_px([(5,2),(4,3),(5,3),(6,3)], fg),  # crown
    *_px([(5,4),(5,5)], fg),  # neck
    *_px([(4,6),(5,6),(6,6)], fg),  # body
    _rect(3, 7, 5, 1, fg),  # base
])

_register("smiley", lambda fg="#FFD700", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7)], fg),
    *_px([(4,4),(6,4)], "#000000"),  # eyes
    *_px([(4,6),(5,6),(6,6)], "#000000"),  # smile
])

_register("sad face", lambda fg="#FFD700", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7)], fg),
    *_px([(4,4),(6,4)], "#000000"),
    *_px([(5,7),(4,6),(6,6)], "#000000"),  # frown
])

_register("winking face", lambda fg="#FFD700", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(4,3),(5,3),(6,3),(7,3),
          (3,4),(4,4),(5,4),(6,4),(7,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7)], fg),
    *_px([(4,4)], "#000000"),  # open eye
    *_px([(6,4)], fg),  # wink (same as face)
    _line(5, 4, 7, 4, "#000000"),  # wink line
    *_px([(4,6),(5,6),(6,6)], "#000000"),
])

_register("piano keys", lambda fg="#FFFFFF", bg="#000000": [
    _fill(bg),
    # White keys
    *[_rect(x, 4, 1, 6, fg) for x in range(1, 9)],
    # Black keys
    *[_rect(x, 4, 1, 3, "#000000") for x in [2, 3, 5, 6, 7]],
])

_register("guitar", lambda fg="#C4A882", bg="#0a0a2a": [
    _fill(bg),
    *_px([(5,1),(5,2),(5,3)], "#888888"),  # neck/tuners
    *_px([(4,4),(5,4),(6,4)], fg),  # neck body
    *_px([(3,5),(4,5),(5,5),(6,5),(7,5),
          (3,6),(4,6),(5,6),(6,6),(7,6),
          (4,7),(5,7),(6,7)], fg),  # body
    *_px([(5,5),(5,6)], "#000000"),  # sound hole
])

_register("eye", lambda fg="#FFFFFF", bg="#0a0a1a": [
    _fill(bg),
    *_px([(4,4),(5,4),(6,4),
          (3,5),(4,5),(5,5),(6,5),(7,5),
          (4,6),(5,6),(6,6)], fg),
    *_px([(5,5)], "#4488FF"),  # iris
    *_px([(5,5)], "#000000"),  # pupil (overrides iris center)
])

_register("hand", lambda fg="#DEB887", bg="#0a0a1a": [
    _fill(bg),
    *_px([(3,2),(4,2),(5,2),(6,2),(7,2)], fg),  # fingertips
    *_px([(3,3),(4,3),(5,3),(6,3),(7,3)], fg),
    *_px([(3,4),(4,4),(5,4),(6,4),(7,4)], fg),
    *_px([(3,5),(4,5),(5,5),(6,5),(7,5)], fg),
    *_px([(4,6),(5,6),(6,6)], fg),  # palm
    *_px([(4,7),(5,7),(6,7)], fg),
    *_px([(2,5),(2,6)], fg),  # thumb
])

_register("clock", lambda fg="#FFFFFF", bg="#0a0a2a": [
    _fill(bg),
    *_px([(4,2),(5,2),(6,2),
          (3,3),(7,3),
          (2,4),(8,4),
          (2,5),(5,5),(8,5),
          (2,6),(8,6),
          (3,7),(7,7),
          (4,8),(5,8),(6,8)], fg),  # outline
    *_px([(5,3),(5,4),(5,5)], "#FF4444"),  # minute hand (12 o'clock)
    *_px([(5,5),(6,5),(7,5)], "#FF4444"),  # hour hand (3 o'clock)
])


# ══════════════════════════════════════════════════════════════════════════
# COLOR MOOD MAPPING
# ══════════════════════════════════════════════════════════════════════════

MOOD_COLORS = {
    "warm": ("#FF6B4A", "#FFE4C4"), "cozy": ("#D88B70", "#FFF0DC"),
    "calm": ("#4A90D9", "#E6E6FA"), "relaxing": ("#008B8B", "#E6E6FA"),
    "energetic": ("#FF4444", "#FFD700"), "romantic": ("#FFB6C1", "#9370DB"),
    "mysterious": ("#483D8B", "#1a1a3a"), "spooky": ("#FF6600", "#1a0a2a"),
    "festive": ("#FF0000", "#00FF00"), "professional": ("#F0F8FF", "#ADD8E6"),
    "peaceful": ("#87CEEB", "#E6E6FA"), "moody": ("#483D8B", "#1a1a3a"),
    "bright": ("#FFFFFF", "#FFD700"), "dark": ("#191970", "#0a0a1a"),
    "soft": ("#FFB6C1", "#E6E6FA"), "vibrant": ("#FF00FF", "#00FFFF"),
    "muted": ("#8B8682", "#DEB887"), "playful": ("#FF69B4", "#FFD700"),
    "dramatic": ("#FF0000", "#000000"), "subtle": ("#DEB887", "#F5F5DC"),
    "intense": ("#FF0000", "#FF4444"), "dreamy": ("#E6E6FA", "#FFB6C1"),
    "nostalgic": ("#DEB887", "#8B4513"), "futuristic": ("#00FFFF", "#0000FF"),
    "zen": ("#228B22", "#F5F5DC"), "melancholy": ("#4A6FA5", "#2F4F4F"),
    "cheerful": ("#FFD700", "#FF6347"), "elegant": ("#C0C0C0", "#000000"),
    "rustic": ("#8B4513", "#DEB887"), "minimalist": ("#F5F5F5", "#333333"),
    "luxurious": ("#FFD700", "#800080"), "whimsical": ("#FF69B4", "#00CED1"),
    "serene": ("#87CEEB", "#F0F8FF"), "bold": ("#FF0000", "#FFD700"),
    "gentle": ("#FFB6C1", "#F5F5DC"), "fiery": ("#FF4444", "#FF6600"),
    "icy": ("#ADD8E6", "#F0FFFF"), "tropical": ("#FF6347", "#00CED1"),
    "earthy": ("#8B4513", "#228B22"), "ethereal": ("#E6E6FA", "#F0F8FF"),
    "gloomy": ("#2F4F4F", "#191970"), "uplifting": ("#FFD700", "#FF6347"),
}

# Color name to hex
COLOR_HEX = {
    "orange": "#FF6B4A", "amber": "#FFBF00", "warm white": "#FFF0DC",
    "golden": "#FFD700", "peach": "#FFDAB9", "coral": "#FF7F50",
    "terracotta": "#CC6644", "copper": "#B87333", "honey": "#EB9605",
    "sunset orange": "#FF5E3A", "burnt sienna": "#E97451",
    "blue": "#4A90D9", "teal": "#008B8B", "cyan": "#00CED1",
    "ice blue": "#B0E0E6", "sky blue": "#87CEEB", "navy": "#191970",
    "aquamarine": "#7FFFD4", "turquoise": "#40E0D0", "arctic blue": "#D0EAFF",
    "steel blue": "#4682B4",
    "lavender": "#E6E6FA", "soft purple": "#9370DB", "lilac": "#C8A2C8",
    "periwinkle": "#CCCCFF", "mauve": "#E0B0FF", "dusty rose": "#DCAE96",
    "sage green": "#B2AC88", "seafoam": "#93E9BE", "powder blue": "#B0E0E6",
    "red": "#FF4444", "magenta": "#FF00FF", "hot pink": "#FF69B4",
    "electric blue": "#0000FF", "neon green": "#39FF14", "bright yellow": "#FFFF00",
    "lime": "#00FF00", "fuchsia": "#FF00FF", "vivid orange": "#FF5F00",
    "forest green": "#228B22", "earth brown": "#8B4513", "moss green": "#8A9A5B",
    "leaf green": "#6B8E23", "olive": "#808000", "pine": "#01796F",
    "emerald": "#50C878", "jade": "#00A86B", "fern": "#4F7942",
    "white": "#FFFFFF", "black": "#000000", "gray": "#888888",
    "dark blue": "#0a0a2a", "dark purple": "#1a0a2a", "dark green": "#0a1a0a",
}

# Activity to mood mapping
ACTIVITY_MOODS = {
    "studying": "professional", "reading": "calm", "meditation": "zen",
    "yoga": "serene", "cooking": "warm", "gaming": "energetic",
    "sleeping": "dark", "working": "professional", "dining": "romantic",
    "partying": "energetic", "relaxing": "calm", "exercising": "energetic",
    "movie watching": "dark", "painting": "dreamy", "writing": "calm",
    "coding": "professional", "napping": "dark", "stretching": "gentle",
    "journaling": "calm", "deep work": "professional", "brainstorming": "energetic",
    "baking": "warm", "tea time": "cozy", "wine tasting": "elegant",
    "board games": "playful", "video call": "professional",
    "podcast listening": "calm", "homework": "professional",
    "practicing guitar": "moody", "doing puzzles": "calm",
}

# Time of day to mood
TIME_MOODS = {
    "morning": "warm", "afternoon": "bright", "evening": "cozy",
    "night": "dark", "late night": "mysterious", "dawn": "gentle",
    "dusk": "romantic", "midnight": "dark", "sunrise": "warm",
    "sunset": "romantic", "golden hour": "warm", "twilight": "mysterious",
    "early morning": "gentle",
}

# Season to mood
SEASON_MOODS = {
    "spring": "gentle", "summer": "bright", "autumn": "warm",
    "fall": "warm", "winter": "icy",
}

# Place to mood
PLACE_MOODS = {
    "beach": "tropical", "forest": "earthy", "mountain cabin": "cozy",
    "city loft": "futuristic", "garden": "gentle", "library": "calm",
    "coffee shop": "cozy", "spa": "serene", "campfire": "warm",
    "underwater cave": "mysterious", "space station": "futuristic",
    "japanese garden": "zen", "northern lights viewing": "ethereal",
    "rooftop terrace": "romantic", "cozy bedroom": "cozy",
    "art studio": "dreamy",
}


# ══════════════════════════════════════════════════════════════════════════
# RESPONSE GENERATORS
# ══════════════════════════════════════════════════════════════════════════

def _make_program(name, steps, loop=None, on_complete=None):
    """Build a program dict."""
    prog = {"name": name, "steps": steps}
    if loop:
        prog["loop"] = loop
    if on_complete:
        prog["on_complete"] = on_complete
    return {"program": prog}


def _pattern_step(sid, pname, params, duration=None):
    step = {"id": sid, "command": {"type": "pattern", "name": pname, "params": params}}
    if duration is not None:
        step["duration"] = duration
    else:
        step["duration"] = None
    return step


def _render_step(sid, elements, duration=None):
    step = {"id": sid, "command": {"type": "render", "elements": elements}}
    if duration is not None:
        step["duration"] = duration
    else:
        step["duration"] = None
    return step


def _mood_to_colors(mood_str):
    """Extract mood colors from a string, trying various lookups."""
    mood_str = mood_str.lower().strip()
    # Direct mood match
    if mood_str in MOOD_COLORS:
        return MOOD_COLORS[mood_str]
    # Partial match
    for key in MOOD_COLORS:
        if key in mood_str:
            return MOOD_COLORS[key]
    # Activity match
    for act, mood in ACTIVITY_MOODS.items():
        if act in mood_str:
            return MOOD_COLORS.get(mood, ("#FF6B4A", "#FFE4C4"))
    # Time match
    for t, mood in TIME_MOODS.items():
        if t in mood_str:
            return MOOD_COLORS.get(mood, ("#FF6B4A", "#FFE4C4"))
    # Season match
    for s, mood in SEASON_MOODS.items():
        if s in mood_str:
            return MOOD_COLORS.get(mood, ("#FF6B4A", "#FFE4C4"))
    # Place match
    for p, mood in PLACE_MOODS.items():
        if p in mood_str:
            return MOOD_COLORS.get(mood, ("#FF6B4A", "#FFE4C4"))
    # Default warm
    return ("#FF6B4A", "#FFE4C4")


def _color_from_name(name):
    """Get hex from color name."""
    name = name.lower().strip()
    if name in COLOR_HEX:
        return COLOR_HEX[name]
    # Partial match
    for key, val in COLOR_HEX.items():
        if key in name or name in key:
            return val
    return "#FF6B4A"


def _pick_pattern(prompt, rng):
    """Choose pattern type and params based on prompt keywords."""
    p = prompt.lower()

    # Explicit pattern requests
    if "breathing" in p or "breathe" in p or "pulsing" in p:
        c1, _ = _mood_to_colors(p)
        speed = rng.choice([2000, 2500, 3000, 3500, 4000])
        if "fast" in p or "rapid" in p or "quick" in p:
            speed = rng.choice([500, 800, 1000])
        elif "slow" in p or "gentle" in p or "calm" in p:
            speed = rng.choice([3000, 4000, 5000])
        return "breathing", {"color": c1, "speed": speed}

    if "wave" in p:
        c1, c2 = _mood_to_colors(p)
        speed = rng.choice([1500, 2000, 2500, 3000])
        return "wave", {"color": c1, "color2": c2, "speed": speed}

    if "rainbow" in p:
        speed = rng.choice([2000, 3000, 4000, 5000])
        if "fast" in p:
            speed = rng.choice([1000, 1500, 2000])
        return "rainbow", {"speed": speed}

    if "sparkle" in p or "twinkl" in p or "star" in p:
        c1, _ = _mood_to_colors(p)
        bg = "#1a1a1a"
        if "dark" in p:
            bg = "#0a0a0a"
        return "sparkle", {"color": c1, "bgColor": bg, "speed": rng.choice([80, 100, 150]), "density": rng.choice([0.08, 0.1, 0.15, 0.2])}

    if "flash" in p or "pulse" in p:
        c1, _ = _mood_to_colors(p)
        return "pulse", {"color": c1, "speed": rng.choice([300, 500, 800])}

    if "gradient" in p or "blend" in p:
        c1, c2 = _mood_to_colors(p)
        return "gradient", {"color": c1, "color2": c2}

    if "solid" in p or "just" in p or "all " in p or "set the color" in p:
        c1, _ = _mood_to_colors(p)
        return "solid", {"color": c1}

    # Color-specific: check if a named color is the main intent
    for cname, chex in COLOR_HEX.items():
        if cname in p and len(p.split()) <= 4:
            return rng.choice(["solid", "breathing"]), {"color": chex} if rng.random() < 0.5 else {"color": chex, "speed": rng.choice([2000, 3000])}

    # Default: choose based on mood
    c1, c2 = _mood_to_colors(p)
    pattern_type = rng.choice(["gradient", "breathing", "solid", "wave"])
    if pattern_type == "gradient":
        return "gradient", {"color": c1, "color2": c2}
    elif pattern_type == "breathing":
        return "breathing", {"color": c1, "speed": rng.choice([2000, 3000, 4000])}
    elif pattern_type == "wave":
        return "wave", {"color": c1, "color2": c2, "speed": rng.choice([2000, 3000])}
    else:
        return "solid", {"color": c1}


def generate_pattern_response(prompt, rng):
    """Generate a single-step pattern program."""
    pname, params = _pick_pattern(prompt, rng)
    name = prompt[:30].title().replace('"', '')
    step = _pattern_step("main", pname, params)
    return _make_program(name, [step])


def generate_render_response(prompt, rng):
    """Generate a render (pixel art) program."""
    p = prompt.lower()

    # Find matching pixel art
    best_match = None
    for art_name in PIXEL_ART_DEFS:
        if art_name in p:
            best_match = art_name
            break

    if not best_match:
        # Fuzzy match: check individual words
        for art_name in PIXEL_ART_DEFS:
            art_words = set(art_name.split())
            prompt_words = set(p.split())
            if art_words & prompt_words:
                best_match = art_name
                break

    if not best_match:
        # Default to a random shape
        best_match = rng.choice(list(PIXEL_ART_DEFS.keys()))

    # Get the elements, optionally with custom colors
    elements_fn = PIXEL_ART_DEFS[best_match]
    fg, bg = None, None

    # Check for color in prompt
    for cname, chex in COLOR_HEX.items():
        if cname in p:
            fg = chex
            break

    if fg:
        try:
            elements = elements_fn(fg=fg)
        except TypeError:
            elements = elements_fn()
    else:
        elements = elements_fn()

    name = best_match.title()
    step = _render_step("show", elements)
    return _make_program(name, [step])


def _parse_duration_ms(text):
    """Parse duration strings to milliseconds."""
    text = text.lower().strip()
    m = re.search(r"(\d+)\s*(second|sec|s\b)", text)
    if m:
        return int(m.group(1)) * 1000
    m = re.search(r"(\d+)\s*(minute|min|m\b)", text)
    if m:
        return int(m.group(1)) * 60000
    m = re.search(r"(\d+)\s*(hour|hr|h\b)", text)
    if m:
        return int(m.group(1)) * 3600000
    return None


def generate_multi_step_response(prompt, rng):
    """Generate a multi-step program (timers, simulations, transitions)."""
    p = prompt.lower()
    c1, c2 = _mood_to_colors(p)

    # ── Countdown ────────────────────────────────────────────────────
    m = re.search(r"countdown\s+(?:from\s+)?(\d+)", p)
    if m:
        n = min(int(m.group(1)), 20)
        steps = []
        for i in range(n, 0, -1):
            steps.append(_render_step(f"n{i}", [
                _fill("#0a0a1a"),
                _text(str(i), 3 if i < 10 else 1, 4, "#FF4444" if i <= 3 else "#FFD700")
            ], 1000))
        steps.append(_render_step("go", [
            _fill("#003300"), _text("GO", 2, 5, "#00FF00")
        ], 2000))
        return _make_program("Countdown", steps,
                             on_complete={"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 2000}}})

    # ── Timer / Pomodoro ─────────────────────────────────────────────
    if "pomodoro" in p or ("timer" in p and ("work" in p or "break" in p or "rest" in p or "focus" in p)):
        dur = _parse_duration_ms(p) or 1500000
        break_dur = rng.choice([300000, 300000, 600000])
        work_color = rng.choice(["#CC3333", "#FF4444", "#D94444"])
        break_color = rng.choice(["#33CC66", "#44BB77", "#228B22"])
        return _make_program("Pomodoro", [
            _pattern_step("work", "solid", {"color": work_color}, dur),
            _pattern_step("break", "breathing", {"color": break_color, "speed": 4000}, break_dur),
        ], loop={"count": 4, "start_step": "work", "end_step": "break"},
           on_complete={"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 2000}}})

    # ── Sleep timer / dimming ────────────────────────────────────────
    if "sleep" in p or "dim" in p:
        total = _parse_duration_ms(p) or 1800000
        n_steps = 5
        step_dur = total // n_steps
        colors = ["#483D8B", "#2F2F5F", "#1a1a3a", "#0d0d1f", "#050510"]
        steps = [_pattern_step(f"dim{i}", "solid", {"color": colors[i]}, step_dur) for i in range(n_steps)]
        return _make_program("Sleep Timer", steps,
                             on_complete={"command": {"type": "pattern", "name": "solid", "params": {"color": "#000000"}}})

    # ── Sunrise ──────────────────────────────────────────────────────
    if "sunrise" in p or "wake" in p or "morning routine" in p:
        dur = _parse_duration_ms(p) or 600000
        step_dur = dur // 4
        return _make_program("Sunrise", [
            _pattern_step("dark", "solid", {"color": "#0a0a1a"}, step_dur),
            _pattern_step("dawn", "gradient", {"color": "#FF6B4A", "color2": "#1a0a2a"}, step_dur),
            _pattern_step("rise", "gradient", {"color": "#FFD700", "color2": "#FF6B4A"}, step_dur),
            _pattern_step("day", "solid", {"color": "#FFFFCC"}, None),
        ])

    # ── Sunset / bedtime ─────────────────────────────────────────────
    if "sunset" in p or "bedtime" in p:
        dur = _parse_duration_ms(p) or 600000
        step_dur = dur // 4
        return _make_program("Sunset", [
            _pattern_step("bright", "solid", {"color": "#FFD700"}, step_dur),
            _pattern_step("orange", "gradient", {"color": "#FF6B4A", "color2": "#FFD700"}, step_dur),
            _pattern_step("dusk", "gradient", {"color": "#483D8B", "color2": "#FF6B4A"}, step_dur),
            _pattern_step("night", "solid", {"color": "#0a0a1a"}, None),
        ])

    # ── Simulation (natural phenomena) ───────────────────────────────
    if "thunderstorm" in p or "thunder" in p or "lightning storm" in p:
        return _make_program("Thunderstorm", [
            _pattern_step("dark", "breathing", {"color": "#1a1a3a", "speed": 3000}, 4000),
            _pattern_step("flash", "pulse", {"color": "#FFFFFF", "speed": 300}, 500),
            _pattern_step("rumble", "sparkle", {"color": "#4444AA", "bgColor": "#0a0a1a", "speed": 80, "density": 0.15}, 3000),
        ], loop={"count": 0, "start_step": "dark", "end_step": "rumble"})

    if "rain" in p and "thunder" not in p:
        return _make_program("Rain", [
            _pattern_step("rain", "sparkle", {"color": "#4488FF", "bgColor": "#0a0a2a", "speed": 60, "density": 0.2}, None),
        ])

    if "aurora" in p or "northern lights" in p:
        return _make_program("Aurora", [
            _pattern_step("green", "wave", {"color": "#00FF88", "color2": "#004466", "speed": 3000}, 5000),
            _pattern_step("purple", "wave", {"color": "#9370DB", "color2": "#004466", "speed": 3000}, 5000),
            _pattern_step("blue", "wave", {"color": "#00CED1", "color2": "#004466", "speed": 3000}, 5000),
        ], loop={"count": 0, "start_step": "green", "end_step": "blue"})

    if "ocean" in p or "sea" in p:
        return _make_program("Ocean Waves", [
            _pattern_step("wave1", "wave", {"color": "#4A90D9", "color2": "#003366", "speed": 3000}, 6000),
            _pattern_step("wave2", "wave", {"color": "#008B8B", "color2": "#003366", "speed": 2500}, 6000),
        ], loop={"count": 0, "start_step": "wave1", "end_step": "wave2"})

    if "campfire" in p or "fireplace" in p or "fire" in p:
        return _make_program("Campfire", [
            _pattern_step("low", "breathing", {"color": "#FF4400", "speed": 2000}, 3000),
            _pattern_step("bright", "pulse", {"color": "#FFAA00", "speed": 400}, 600),
            _pattern_step("ember", "sparkle", {"color": "#FF6600", "bgColor": "#1a0a00", "speed": 100, "density": 0.12}, 4000),
        ], loop={"count": 0, "start_step": "low", "end_step": "ember"})

    if "snow" in p or "blizzard" in p:
        return _make_program("Snowfall", [
            _pattern_step("snow", "sparkle", {"color": "#FFFFFF", "bgColor": "#1a2a3a", "speed": 120, "density": 0.15}, None),
        ])

    if "meteor" in p:
        return _make_program("Meteor Shower", [
            _pattern_step("sky", "solid", {"color": "#0a0a1a"}, 3000),
            _pattern_step("streak", "pulse", {"color": "#FFFFFF", "speed": 200}, 400),
            _pattern_step("glow", "sparkle", {"color": "#FFD700", "bgColor": "#0a0a1a", "speed": 80, "density": 0.05}, 2000),
        ], loop={"count": 0, "start_step": "sky", "end_step": "glow"})

    if "volcano" in p or "lava" in p:
        return _make_program("Volcano", [
            _pattern_step("rumble", "breathing", {"color": "#FF2200", "speed": 1500}, 3000),
            _pattern_step("erupt", "pulse", {"color": "#FF6600", "speed": 300}, 500),
            _pattern_step("flow", "wave", {"color": "#FF4400", "color2": "#FF0000", "speed": 1500}, 4000),
        ], loop={"count": 0, "start_step": "rumble", "end_step": "flow"})

    # ── Transitions ──────────────────────────────────────────────────
    if "transition" in p or "fade from" in p:
        # Extract two colors
        colors_found = []
        for cname, chex in COLOR_HEX.items():
            if cname in p:
                colors_found.append(chex)
        if len(colors_found) < 2:
            colors_found = [c1, c2]
        dur = _parse_duration_ms(p) or 30000
        return _make_program("Transition", [
            _pattern_step("start", "solid", {"color": colors_found[0]}, dur // 2),
            _pattern_step("end", "solid", {"color": colors_found[1]}, None),
        ])

    if "alternate" in p or "cycle through" in p:
        colors_found = []
        for cname, chex in COLOR_HEX.items():
            if cname in p and chex not in colors_found:
                colors_found.append(chex)
        if len(colors_found) < 2:
            colors_found = [c1, c2]
        steps = [_pattern_step(f"c{i}", "solid", {"color": c}, 2000) for i, c in enumerate(colors_found[:4])]
        return _make_program("Color Cycle", steps,
                             loop={"count": 0, "start_step": steps[0]["id"], "end_step": steps[-1]["id"]})

    # ── Party / disco / celebration ──────────────────────────────────
    if "party" in p or "disco" in p or "rave" in p or "celebration" in p or "celebrate" in p:
        return _make_program("Party Mode", [
            _pattern_step("flash1", "pulse", {"color": "#FF00FF", "speed": 300}, 500),
            _pattern_step("flash2", "pulse", {"color": "#00FFFF", "speed": 300}, 500),
            _pattern_step("flash3", "pulse", {"color": "#FFD700", "speed": 300}, 500),
            _pattern_step("rainbow", "rainbow", {"speed": 1000}, 3000),
        ], loop={"count": 0, "start_step": "flash1", "end_step": "rainbow"})

    # ── Breathing exercise ───────────────────────────────────────────
    if "breathing exercise" in p or "box breathing" in p:
        return _make_program("Breathing Exercise", [
            _pattern_step("inhale", "solid", {"color": "#4A90D9"}, 4000),
            _pattern_step("hold", "solid", {"color": "#228B22"}, 4000),
            _pattern_step("exhale", "breathing", {"color": "#4A90D9", "speed": 4000}, 4000),
            _pattern_step("rest", "solid", {"color": "#1a1a3a"}, 4000),
        ], loop={"count": 0, "start_step": "inhale", "end_step": "rest"})

    # ── Traffic light ────────────────────────────────────────────────
    if "traffic" in p:
        return _make_program("Traffic Light", [
            _pattern_step("green", "solid", {"color": "#00FF00"}, 5000),
            _pattern_step("yellow", "solid", {"color": "#FFD700"}, 2000),
            _pattern_step("red", "solid", {"color": "#FF0000"}, 5000),
        ], loop={"count": 0, "start_step": "green", "end_step": "red"})

    # ── Emergency lights ─────────────────────────────────────────────
    if "police" in p or "emergency" in p or "ambulance" in p or "fire truck" in p:
        return _make_program("Emergency Lights", [
            _pattern_step("red", "pulse", {"color": "#FF0000", "speed": 200}, 400),
            _pattern_step("blue", "pulse", {"color": "#0000FF", "speed": 200}, 400),
        ], loop={"count": 0, "start_step": "red", "end_step": "blue"})

    # ── Holiday themes ───────────────────────────────────────────────
    if "christmas" in p:
        return _make_program("Christmas", [
            _pattern_step("red", "solid", {"color": "#FF0000"}, 3000),
            _pattern_step("green", "solid", {"color": "#00FF00"}, 3000),
            _pattern_step("sparkle", "sparkle", {"color": "#FFD700", "bgColor": "#003300", "speed": 100, "density": 0.15}, 4000),
        ], loop={"count": 0, "start_step": "red", "end_step": "sparkle"})

    if "halloween" in p:
        return _make_program("Halloween", [
            _pattern_step("orange", "breathing", {"color": "#FF6600", "speed": 2000}, 4000),
            _pattern_step("flash", "pulse", {"color": "#00FF00", "speed": 300}, 500),
            _pattern_step("spooky", "sparkle", {"color": "#9900CC", "bgColor": "#0a0a0a", "speed": 80, "density": 0.1}, 3000),
        ], loop={"count": 0, "start_step": "orange", "end_step": "spooky"})

    if "valentine" in p:
        return _make_program("Valentine", [
            _pattern_step("pink", "breathing", {"color": "#FF69B4", "speed": 3000}, 5000),
            _pattern_step("red", "breathing", {"color": "#FF2266", "speed": 3000}, 5000),
        ], loop={"count": 0, "start_step": "pink", "end_step": "red"})

    if "birthday" in p:
        return _make_program("Birthday", [
            _pattern_step("party1", "pulse", {"color": "#FF69B4", "speed": 300}, 500),
            _pattern_step("party2", "pulse", {"color": "#FFD700", "speed": 300}, 500),
            _pattern_step("party3", "pulse", {"color": "#00CED1", "speed": 300}, 500),
            _pattern_step("rainbow", "rainbow", {"speed": 1500}, 4000),
        ], loop={"count": 0, "start_step": "party1", "end_step": "rainbow"})

    if "new year" in p:
        return _make_program("New Year", [
            _pattern_step("gold", "sparkle", {"color": "#FFD700", "bgColor": "#0a0a1a", "speed": 80, "density": 0.2}, 3000),
            _pattern_step("flash", "pulse", {"color": "#FFFFFF", "speed": 200}, 400),
            _pattern_step("rainbow", "rainbow", {"speed": 1500}, 3000),
        ], loop={"count": 0, "start_step": "gold", "end_step": "rainbow"})

    # ── Meditation ───────────────────────────────────────────────────
    if "meditation" in p:
        dur = _parse_duration_ms(p) or 600000
        return _make_program("Meditation", [
            _pattern_step("calm", "breathing", {"color": "#4A90D9", "speed": 5000}, dur),
        ], on_complete={"command": {"type": "pattern", "name": "solid", "params": {"color": "#E6E6FA"}}})

    # ── Generic multi-step: use mood colors in a sequence ────────────
    return _make_program(prompt[:30].title().replace('"', ''), [
        _pattern_step("phase1", "gradient", {"color": c1, "color2": c2}, rng.choice([5000, 8000, 10000])),
        _pattern_step("phase2", "breathing", {"color": c1, "speed": rng.choice([2000, 3000, 4000])}, rng.choice([5000, 8000, 10000])),
        _pattern_step("phase3", "wave", {"color": c1, "color2": c2, "speed": rng.choice([2000, 3000])}, None),
    ])


def generate_mixed_response(prompt, rng):
    """Generate a program that combines render + pattern."""
    p = prompt.lower()

    # Find any pixel art reference
    art_name = None
    for name in PIXEL_ART_DEFS:
        if name in p:
            art_name = name
            break
    if not art_name:
        for name in PIXEL_ART_DEFS:
            for word in name.split():
                if word in p and len(word) > 2:
                    art_name = name
                    break
            if art_name:
                break
    if not art_name:
        art_name = rng.choice(list(PIXEL_ART_DEFS.keys()))

    elements = PIXEL_ART_DEFS[art_name]()
    c1, c2 = _mood_to_colors(p)
    dur = _parse_duration_ms(p) or 5000

    steps = [_render_step("show", elements, dur)]

    # Add a pattern step after
    pname, params = _pick_pattern(p, rng)
    steps.append(_pattern_step("after", pname, params))

    return _make_program(f"{art_name.title()} Then {pname.title()}", steps)


def generate_text_response(prompt, rng):
    """Generate a text display / clock program."""
    p = prompt.lower()

    # Clock
    m = re.search(r"(\d{1,2}):(\d{2})", p)
    if m:
        hr, mn = m.group(1), m.group(2)
        color = rng.choice(["#00FF88", "#FFD700", "#FF4444", "#44AAFF", "#FFFFFF"])
        return _make_program("Clock", [
            _render_step("show", [
                _fill("#0a0a1a"),
                _text(hr, 2, 2, color),
                {"type": "pixel", "x": 5, "y": 5, "color": color},
                {"type": "pixel", "x": 5, "y": 7, "color": color},
                _text(mn, 2, 8, color),
            ])
        ])

    # Temperature display
    m = re.search(r"(\-?\d+)\s*(?:degree|°|deg)", p)
    if m:
        temp = m.group(1)
        color = "#FF4444" if int(temp) > 25 else "#4488FF" if int(temp) < 10 else "#FFD700"
        return _make_program("Temperature", [
            _render_step("show", [
                _fill("#0a0a1a"),
                _text(temp, 1, 3, color),
                _text("C", 6, 8, "#888888"),
            ])
        ])

    # Score
    m = re.search(r"score\s*(\d+)\s*[-:]\s*(\d+)", p)
    if m:
        s1, s2 = m.group(1), m.group(2)
        return _make_program("Score", [
            _render_step("show", [
                _fill("#0a0a1a"),
                _text(s1, 1, 3, "#FF4444"),
                _text("-", 4, 6, "#FFFFFF"),
                _text(s2, 6, 3, "#4488FF"),
            ])
        ])

    # Number display
    m = re.search(r"number\s*(\d+)", p)
    if m:
        num = m.group(1)
        return _make_program("Number", [
            _render_step("show", [
                _fill("#0a0a1a"),
                _text(num, max(0, 5 - len(num) * 2), 5, "#FFD700"),
            ])
        ])

    # Generic text
    text = None
    for word in ["HI", "HELLO", "LOVE", "PEACE", "YES", "NO", "OK", "GO",
                 "COOL", "WOW", "YAY", "HEY", "BYE", "STOP", "PLAY", "WIN",
                 "HOME", "LAMP", "MOON", "STAR", "FIRE", "RAIN", "SUN"]:
        if word.lower() in p:
            text = word
            break

    m = re.search(r"letter\s+([a-zA-Z])", p)
    if m:
        text = m.group(1).upper()

    if not text:
        # Try to extract text from quotes or after "display"/"show"
        m = re.search(r"(?:display|show|write|text)\s+(\w+)", p)
        if m:
            text = m.group(1).upper()[:4]

    if not text:
        text = "HI"

    # Color from prompt
    color = "#FFFFFF"
    for cname, chex in COLOR_HEX.items():
        if cname in p:
            color = chex
            break

    bg = "#0a0a1a"
    for bg_name, bg_hex in [("black", "#000000"), ("dark blue", "#0a0a2a"),
                             ("dark purple", "#1a0a2a"), ("dark green", "#0a1a0a")]:
        if bg_name in p:
            bg = bg_hex

    # Calculate x position to roughly center the text (3px per char + 1px gap)
    text_width = len(text) * 4 - 1
    x = max(0, (10 - text_width) // 2)

    return _make_program(f"Display {text}", [
        _render_step("show", [
            _fill(bg),
            _text(text, x, 5, color),
        ])
    ])


# ══════════════════════════════════════════════════════════════════════════
# MAIN: Read prompts, generate responses, save
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate Opus-quality responses")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--input", default=None, help="Input prompts file")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # Load prompts
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    input_path = args.input or os.path.join(data_dir, "prompts.jsonl")

    prompts = []
    with open(input_path) as f:
        for line in f:
            prompts.append(json.loads(line.strip()))

    print(f"  Loaded {len(prompts)} prompts from {input_path}")

    # Route each prompt to the appropriate generator
    GENERATORS = {
        "pattern": generate_pattern_response,
        "render": generate_render_response,
        "multi_step": generate_multi_step_response,
        "mixed": generate_mixed_response,
        "text": generate_text_response,
        "creative": generate_pattern_response,  # creative prompts → pattern
        "edge_case": generate_pattern_response,  # edge cases → pattern (safe default)
    }

    results = []
    errors = 0

    for i, item in enumerate(prompts):
        prompt = item["prompt"]
        category = item["category"]

        gen_fn = GENERATORS.get(category, generate_pattern_response)

        try:
            program = gen_fn(prompt, rng)
            # Validate basic structure
            assert "program" in program
            assert "steps" in program["program"]
            assert len(program["program"]["steps"]) > 0
            response_json = json.dumps(program, separators=(',', ':'))

            results.append({
                "prompt": prompt,
                "category": category,
                "response": response_json,
                "program": program,
            })
        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"  ERROR on prompt [{i}] '{prompt[:50]}': {e}")

        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(prompts)}...")

    # Save
    out_path = os.path.join(data_dir, "raw_responses.jsonl")
    with open(out_path, "w") as f:
        for r in results:
            # Save without the parsed program (just prompt + response string)
            f.write(json.dumps({
                "prompt": r["prompt"],
                "category": r["category"],
                "response": r["response"],
            }) + "\n")

    print(f"\n  Generated {len(results)} responses ({errors} errors)")
    print(f"  Saved to: {out_path}")

    # Category stats
    cats = {}
    for r in results:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print("\n  Category breakdown:")
    for cat, cnt in sorted(cats.items()):
        print(f"    {cat:12s}: {cnt:4d}")


if __name__ == "__main__":
    main()

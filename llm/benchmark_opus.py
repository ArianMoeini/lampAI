"""
Benchmark: Claude Opus 4.6 generated programs for the same 21 prompts.
These programs are crafted with full understanding of the 10x14 grid constraints.

Usage:
  python3 benchmark_opus.py          # Run all 21, 5s pause
  python3 benchmark_opus.py --fast   # 2s pause
  python3 benchmark_opus.py --index 5  # Run just one
"""

import json
import time
import sys
import argparse
import urllib.request
import urllib.error

LAMP_SERVER_URL = "http://localhost:3001"

TEST_CASES = [
    # ── Pixel Art (10) ──────────────────────────────────────────────
    {
        "id": 1, "category": "pixel_art", "prompt": "show a star",
        "program": {
            "program": {
                "name": "Star",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a0a2a"},
                        {"type": "pixel", "x": 5, "y": 1, "color": "#FFD700"},
                        {"type": "pixel", "x": 4, "y": 2, "color": "#FFD700"},
                        {"type": "pixel", "x": 5, "y": 2, "color": "#FFD700"},
                        {"type": "pixel", "x": 6, "y": 2, "color": "#FFD700"},
                        {"type": "rect", "x": 2, "y": 3, "w": 7, "h": 1, "color": "#FFD700"},
                        {"type": "pixel", "x": 3, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 4, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 5, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 6, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 7, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 3, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 5, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 7, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 2, "y": 6, "color": "#FFD700"},
                        {"type": "pixel", "x": 5, "y": 6, "color": "#FFD700"},
                        {"type": "pixel", "x": 8, "y": 6, "color": "#FFD700"},
                        {"type": "pixel", "x": 2, "y": 7, "color": "#FFD700"},
                        {"type": "pixel", "x": 8, "y": 7, "color": "#FFD700"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 2, "category": "pixel_art", "prompt": "draw a smiley face",
        "program": {
            "program": {
                "name": "Smiley",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a0a1a"},
                        # Round face outline
                        {"type": "rect", "x": 3, "y": 2, "w": 5, "h": 1, "color": "#FFD700"},
                        {"type": "pixel", "x": 2, "y": 3, "color": "#FFD700"},
                        {"type": "pixel", "x": 8, "y": 3, "color": "#FFD700"},
                        {"type": "pixel", "x": 1, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 9, "y": 4, "color": "#FFD700"},
                        {"type": "pixel", "x": 1, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 9, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 1, "y": 6, "color": "#FFD700"},
                        {"type": "pixel", "x": 9, "y": 6, "color": "#FFD700"},
                        {"type": "pixel", "x": 1, "y": 7, "color": "#FFD700"},
                        {"type": "pixel", "x": 9, "y": 7, "color": "#FFD700"},
                        {"type": "pixel", "x": 1, "y": 8, "color": "#FFD700"},
                        {"type": "pixel", "x": 9, "y": 8, "color": "#FFD700"},
                        {"type": "pixel", "x": 2, "y": 9, "color": "#FFD700"},
                        {"type": "pixel", "x": 8, "y": 9, "color": "#FFD700"},
                        {"type": "rect", "x": 3, "y": 10, "w": 5, "h": 1, "color": "#FFD700"},
                        # Eyes
                        {"type": "pixel", "x": 3, "y": 4, "color": "#FFFFFF"},
                        {"type": "pixel", "x": 3, "y": 5, "color": "#FFFFFF"},
                        {"type": "pixel", "x": 7, "y": 4, "color": "#FFFFFF"},
                        {"type": "pixel", "x": 7, "y": 5, "color": "#FFFFFF"},
                        # Mouth - smile curve
                        {"type": "pixel", "x": 3, "y": 7, "color": "#FF6347"},
                        {"type": "pixel", "x": 4, "y": 8, "color": "#FF6347"},
                        {"type": "pixel", "x": 5, "y": 8, "color": "#FF6347"},
                        {"type": "pixel", "x": 6, "y": 8, "color": "#FF6347"},
                        {"type": "pixel", "x": 7, "y": 7, "color": "#FF6347"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 3, "category": "pixel_art", "prompt": "show an arrow pointing up",
        "program": {
            "program": {
                "name": "Arrow Up",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a0a1a"},
                        # Arrowhead
                        {"type": "pixel", "x": 5, "y": 1, "color": "#00FF88"},
                        {"type": "pixel", "x": 4, "y": 2, "color": "#00FF88"},
                        {"type": "pixel", "x": 5, "y": 2, "color": "#00FF88"},
                        {"type": "pixel", "x": 6, "y": 2, "color": "#00FF88"},
                        {"type": "pixel", "x": 3, "y": 3, "color": "#00FF88"},
                        {"type": "pixel", "x": 5, "y": 3, "color": "#00FF88"},
                        {"type": "pixel", "x": 7, "y": 3, "color": "#00FF88"},
                        {"type": "pixel", "x": 2, "y": 4, "color": "#00FF88"},
                        {"type": "pixel", "x": 5, "y": 4, "color": "#00FF88"},
                        {"type": "pixel", "x": 8, "y": 4, "color": "#00FF88"},
                        # Shaft
                        {"type": "rect", "x": 4, "y": 5, "w": 3, "h": 7, "color": "#00FF88"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 4, "category": "pixel_art", "prompt": "draw a house",
        "program": {
            "program": {
                "name": "House",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#87CEEB"},
                        # Roof - triangle
                        {"type": "pixel", "x": 5, "y": 1, "color": "#8B0000"},
                        {"type": "rect", "x": 4, "y": 2, "w": 3, "h": 1, "color": "#8B0000"},
                        {"type": "rect", "x": 3, "y": 3, "w": 5, "h": 1, "color": "#8B0000"},
                        {"type": "rect", "x": 2, "y": 4, "w": 7, "h": 1, "color": "#8B0000"},
                        # Walls
                        {"type": "rect", "x": 2, "y": 5, "w": 7, "h": 6, "color": "#DEB887"},
                        # Door
                        {"type": "rect", "x": 4, "y": 8, "w": 2, "h": 3, "color": "#8B4513"},
                        {"type": "pixel", "x": 5, "y": 9, "color": "#FFD700"},
                        # Window
                        {"type": "rect", "x": 6, "y": 6, "w": 2, "h": 2, "color": "#ADD8E6"},
                        # Ground
                        {"type": "rect", "x": 0, "y": 11, "w": 10, "h": 3, "color": "#228B22"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 5, "category": "pixel_art", "prompt": "show a music note",
        "program": {
            "program": {
                "name": "Music Note",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a0a2a"},
                        # Eighth note - flag
                        {"type": "rect", "x": 7, "y": 2, "w": 2, "h": 1, "color": "#FF69B4"},
                        {"type": "pixel", "x": 8, "y": 3, "color": "#FF69B4"},
                        {"type": "pixel", "x": 7, "y": 4, "color": "#FF69B4"},
                        # Stem
                        {"type": "rect", "x": 6, "y": 2, "w": 1, "h": 8, "color": "#FFFFFF"},
                        # Note head (oval)
                        {"type": "pixel", "x": 4, "y": 9, "color": "#FF69B4"},
                        {"type": "pixel", "x": 5, "y": 9, "color": "#FF69B4"},
                        {"type": "pixel", "x": 3, "y": 10, "color": "#FF69B4"},
                        {"type": "pixel", "x": 4, "y": 10, "color": "#FF69B4"},
                        {"type": "pixel", "x": 5, "y": 10, "color": "#FF69B4"},
                        {"type": "pixel", "x": 6, "y": 10, "color": "#FF69B4"},
                        {"type": "pixel", "x": 4, "y": 11, "color": "#FF69B4"},
                        {"type": "pixel", "x": 5, "y": 11, "color": "#FF69B4"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 6, "category": "pixel_art", "prompt": "draw a cat face",
        "program": {
            "program": {
                "name": "Cat Face",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a2e"},
                        # Ears
                        {"type": "pixel", "x": 2, "y": 1, "color": "#FFA500"},
                        {"type": "pixel", "x": 8, "y": 1, "color": "#FFA500"},
                        {"type": "pixel", "x": 2, "y": 2, "color": "#FFA500"},
                        {"type": "pixel", "x": 3, "y": 2, "color": "#FFA500"},
                        {"type": "pixel", "x": 7, "y": 2, "color": "#FFA500"},
                        {"type": "pixel", "x": 8, "y": 2, "color": "#FFA500"},
                        # Head
                        {"type": "rect", "x": 2, "y": 3, "w": 7, "h": 6, "color": "#FFA500"},
                        # Inner ears
                        {"type": "pixel", "x": 2, "y": 2, "color": "#FFB6C1"},
                        {"type": "pixel", "x": 8, "y": 2, "color": "#FFB6C1"},
                        # Eyes
                        {"type": "pixel", "x": 3, "y": 4, "color": "#00FF00"},
                        {"type": "pixel", "x": 4, "y": 4, "color": "#000000"},
                        {"type": "pixel", "x": 7, "y": 4, "color": "#000000"},
                        {"type": "pixel", "x": 6, "y": 4, "color": "#00FF00"},
                        # Nose
                        {"type": "pixel", "x": 5, "y": 6, "color": "#FF69B4"},
                        # Mouth
                        {"type": "pixel", "x": 4, "y": 7, "color": "#1a1a2e"},
                        {"type": "pixel", "x": 5, "y": 7, "color": "#1a1a2e"},
                        {"type": "pixel", "x": 6, "y": 7, "color": "#1a1a2e"},
                        # Whiskers
                        {"type": "line", "x1": 0, "y1": 5, "x2": 2, "y2": 6, "color": "#FFFFFF"},
                        {"type": "line", "x1": 0, "y1": 7, "x2": 2, "y2": 6, "color": "#FFFFFF"},
                        {"type": "line", "x1": 8, "y1": 6, "x2": 9, "y2": 5, "color": "#FFFFFF"},
                        {"type": "line", "x1": 8, "y1": 6, "x2": 9, "y2": 7, "color": "#FFFFFF"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 7, "category": "pixel_art", "prompt": "show a sun",
        "program": {
            "program": {
                "name": "Sun",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a3a"},
                        # Sun core
                        {"type": "rect", "x": 4, "y": 5, "w": 3, "h": 3, "color": "#FFD700"},
                        {"type": "pixel", "x": 3, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 7, "y": 5, "color": "#FFD700"},
                        {"type": "pixel", "x": 3, "y": 7, "color": "#FFD700"},
                        {"type": "pixel", "x": 7, "y": 7, "color": "#FFD700"},
                        # Rays - cardinal
                        {"type": "pixel", "x": 5, "y": 2, "color": "#FFA500"},
                        {"type": "pixel", "x": 5, "y": 3, "color": "#FFA500"},
                        {"type": "pixel", "x": 5, "y": 10, "color": "#FFA500"},
                        {"type": "pixel", "x": 5, "y": 9, "color": "#FFA500"},
                        {"type": "pixel", "x": 1, "y": 6, "color": "#FFA500"},
                        {"type": "pixel", "x": 2, "y": 6, "color": "#FFA500"},
                        {"type": "pixel", "x": 8, "y": 6, "color": "#FFA500"},
                        {"type": "pixel", "x": 9, "y": 6, "color": "#FFA500"},
                        # Rays - diagonal
                        {"type": "pixel", "x": 2, "y": 3, "color": "#FF8C00"},
                        {"type": "pixel", "x": 8, "y": 3, "color": "#FF8C00"},
                        {"type": "pixel", "x": 2, "y": 9, "color": "#FF8C00"},
                        {"type": "pixel", "x": 8, "y": 9, "color": "#FF8C00"},
                        {"type": "pixel", "x": 3, "y": 4, "color": "#FF8C00"},
                        {"type": "pixel", "x": 7, "y": 4, "color": "#FF8C00"},
                        {"type": "pixel", "x": 3, "y": 8, "color": "#FF8C00"},
                        {"type": "pixel", "x": 7, "y": 8, "color": "#FF8C00"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 8, "category": "pixel_art", "prompt": "draw a tree",
        "program": {
            "program": {
                "name": "Tree",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#87CEEB"},
                        # Tree crown - layered triangle
                        {"type": "pixel", "x": 5, "y": 1, "color": "#228B22"},
                        {"type": "rect", "x": 4, "y": 2, "w": 3, "h": 1, "color": "#228B22"},
                        {"type": "rect", "x": 3, "y": 3, "w": 5, "h": 1, "color": "#228B22"},
                        {"type": "rect", "x": 2, "y": 4, "w": 7, "h": 1, "color": "#2E8B57"},
                        {"type": "rect", "x": 3, "y": 5, "w": 5, "h": 1, "color": "#2E8B57"},
                        {"type": "rect", "x": 2, "y": 6, "w": 7, "h": 1, "color": "#006400"},
                        {"type": "rect", "x": 1, "y": 7, "w": 9, "h": 1, "color": "#006400"},
                        # Trunk
                        {"type": "rect", "x": 4, "y": 8, "w": 3, "h": 3, "color": "#8B4513"},
                        # Ground
                        {"type": "rect", "x": 0, "y": 11, "w": 10, "h": 3, "color": "#228B22"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 9, "category": "pixel_art", "prompt": "show a lightning bolt",
        "program": {
            "program": {
                "name": "Lightning Bolt",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a0a2a"},
                        # Lightning bolt shape
                        {"type": "rect", "x": 4, "y": 1, "w": 4, "h": 1, "color": "#FFD700"},
                        {"type": "rect", "x": 3, "y": 2, "w": 4, "h": 1, "color": "#FFD700"},
                        {"type": "rect", "x": 2, "y": 3, "w": 4, "h": 1, "color": "#FFD700"},
                        {"type": "rect", "x": 2, "y": 4, "w": 6, "h": 1, "color": "#FFFF00"},
                        {"type": "rect", "x": 3, "y": 5, "w": 6, "h": 1, "color": "#FFFF00"},
                        {"type": "rect", "x": 5, "y": 6, "w": 4, "h": 1, "color": "#FFD700"},
                        {"type": "rect", "x": 4, "y": 7, "w": 4, "h": 1, "color": "#FFD700"},
                        {"type": "rect", "x": 3, "y": 8, "w": 4, "h": 1, "color": "#FFD700"},
                        {"type": "rect", "x": 4, "y": 9, "w": 3, "h": 1, "color": "#FFA500"},
                        {"type": "rect", "x": 5, "y": 10, "w": 2, "h": 1, "color": "#FFA500"},
                        {"type": "pixel", "x": 5, "y": 11, "color": "#FF8C00"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 10, "category": "pixel_art", "prompt": "draw a skull",
        "program": {
            "program": {
                "name": "Skull",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a0a0a"},
                        # Cranium
                        {"type": "rect", "x": 3, "y": 1, "w": 5, "h": 1, "color": "#EEEEEE"},
                        {"type": "rect", "x": 2, "y": 2, "w": 7, "h": 1, "color": "#EEEEEE"},
                        {"type": "rect", "x": 1, "y": 3, "w": 9, "h": 4, "color": "#EEEEEE"},
                        # Eye sockets
                        {"type": "rect", "x": 2, "y": 4, "w": 2, "h": 2, "color": "#0a0a0a"},
                        {"type": "rect", "x": 6, "y": 4, "w": 2, "h": 2, "color": "#0a0a0a"},
                        # Nose
                        {"type": "pixel", "x": 4, "y": 6, "color": "#0a0a0a"},
                        {"type": "pixel", "x": 5, "y": 6, "color": "#0a0a0a"},
                        # Jaw
                        {"type": "rect", "x": 2, "y": 7, "w": 7, "h": 1, "color": "#DDDDDD"},
                        {"type": "rect", "x": 2, "y": 8, "w": 7, "h": 2, "color": "#DDDDDD"},
                        # Teeth
                        {"type": "pixel", "x": 3, "y": 8, "color": "#0a0a0a"},
                        {"type": "pixel", "x": 5, "y": 8, "color": "#0a0a0a"},
                        {"type": "pixel", "x": 7, "y": 8, "color": "#0a0a0a"},
                        {"type": "pixel", "x": 3, "y": 9, "color": "#0a0a0a"},
                        {"type": "pixel", "x": 5, "y": 9, "color": "#0a0a0a"},
                        {"type": "pixel", "x": 7, "y": 9, "color": "#0a0a0a"},
                    ]},
                    "duration": None
                }]
            }
        }
    },

    # ── Analog Clock (1) ────────────────────────────────────────────
    {
        "id": 11, "category": "analog_clock", "prompt": "show an analog clock at 3 o'clock",
        "program": {
            "program": {
                "name": "Analog Clock 3:00",
                "steps": [{
                    "id": "show",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a0a2a"},
                        # Clock face circle
                        {"type": "rect", "x": 3, "y": 1, "w": 5, "h": 1, "color": "#333333"},
                        {"type": "pixel", "x": 2, "y": 2, "color": "#333333"},
                        {"type": "rect", "x": 3, "y": 2, "w": 5, "h": 1, "color": "#1a1a3a"},
                        {"type": "pixel", "x": 8, "y": 2, "color": "#333333"},
                        {"type": "pixel", "x": 1, "y": 3, "color": "#333333"},
                        {"type": "pixel", "x": 9, "y": 3, "color": "#333333"},
                        {"type": "pixel", "x": 1, "y": 4, "color": "#333333"},
                        {"type": "pixel", "x": 9, "y": 4, "color": "#333333"},
                        {"type": "pixel", "x": 1, "y": 5, "color": "#333333"},
                        {"type": "pixel", "x": 9, "y": 5, "color": "#333333"},
                        {"type": "pixel", "x": 1, "y": 6, "color": "#333333"},
                        {"type": "pixel", "x": 9, "y": 6, "color": "#333333"},
                        {"type": "pixel", "x": 1, "y": 7, "color": "#333333"},
                        {"type": "pixel", "x": 9, "y": 7, "color": "#333333"},
                        {"type": "pixel", "x": 1, "y": 8, "color": "#333333"},
                        {"type": "pixel", "x": 9, "y": 8, "color": "#333333"},
                        {"type": "pixel", "x": 2, "y": 9, "color": "#333333"},
                        {"type": "pixel", "x": 8, "y": 9, "color": "#333333"},
                        {"type": "rect", "x": 3, "y": 10, "w": 5, "h": 1, "color": "#333333"},
                        # 12 o'clock marker
                        {"type": "pixel", "x": 5, "y": 2, "color": "#FFFFFF"},
                        # 3 o'clock marker
                        {"type": "pixel", "x": 8, "y": 5, "color": "#FFFFFF"},
                        # 6 o'clock marker
                        {"type": "pixel", "x": 5, "y": 9, "color": "#FFFFFF"},
                        # 9 o'clock marker
                        {"type": "pixel", "x": 2, "y": 5, "color": "#FFFFFF"},
                        # Center dot
                        {"type": "pixel", "x": 5, "y": 5, "color": "#FF4444"},
                        # Minute hand - pointing up (12)
                        {"type": "pixel", "x": 5, "y": 4, "color": "#FFFFFF"},
                        {"type": "pixel", "x": 5, "y": 3, "color": "#FFFFFF"},
                        # Hour hand - pointing right (3)
                        {"type": "pixel", "x": 6, "y": 5, "color": "#CCCCCC"},
                        {"type": "pixel", "x": 7, "y": 5, "color": "#CCCCCC"},
                    ]},
                    "duration": None
                }]
            }
        }
    },

    # ── Multi-step (10) ─────────────────────────────────────────────
    {
        "id": 12, "category": "multi_step", "prompt": "be a pomodoro timer",
        "program": {
            "program": {
                "name": "Pomodoro",
                "steps": [
                    {"id": "work", "command": {"type": "pattern", "name": "solid", "params": {"color": "#CC3333"}}, "duration": 1500000},
                    {"id": "work_done", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 300}}, "duration": 1000},
                    {"id": "break", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#33CC66", "speed": 4000}}, "duration": 300000},
                    {"id": "break_done", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 300}}, "duration": 1000},
                ],
                "loop": {"count": 4, "start_step": "work", "end_step": "break_done"},
                "on_complete": {"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 2000}}}
            }
        }
    },
    {
        "id": 13, "category": "multi_step", "prompt": "simulate a sunrise",
        "program": {
            "program": {
                "name": "Sunrise",
                "steps": [
                    {"id": "night", "command": {"type": "pattern", "name": "solid", "params": {"color": "#0a0a2a"}}, "duration": 3000},
                    {"id": "predawn", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#1a0a2a", "color2": "#2d1b4e"}}, "duration": 4000},
                    {"id": "dawn", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#4a1942", "color2": "#ff6b4a"}}, "duration": 5000},
                    {"id": "horizon", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#FF4500", "color2": "#FFD700"}}, "duration": 5000},
                    {"id": "morning", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#FFD700", "color2": "#87CEEB"}}, "duration": 5000},
                    {"id": "day", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#87CEEB", "color2": "#FFFFFF"}}, "duration": None},
                ]
            }
        }
    },
    {
        "id": 14, "category": "multi_step", "prompt": "create a meditation session",
        "program": {
            "program": {
                "name": "Meditation",
                "steps": [
                    {"id": "settle", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#4A90D9", "speed": 4000}}, "duration": 10000},
                    {"id": "deep", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#008B8B", "speed": 6000}}, "duration": 20000},
                    {"id": "stillness", "command": {"type": "pattern", "name": "solid", "params": {"color": "#191970"}}, "duration": 30000},
                    {"id": "emerge", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#E6E6FA", "speed": 3000}}, "duration": 10000},
                ],
                "on_complete": {"command": {"type": "pattern", "name": "gradient", "params": {"color": "#E6E6FA", "color2": "#FFFFFF"}}}
            }
        }
    },
    {
        "id": 15, "category": "multi_step", "prompt": "party mode",
        "program": {
            "program": {
                "name": "Party Mode",
                "steps": [
                    {"id": "flash1", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FF00FF", "speed": 200}}, "duration": 500},
                    {"id": "rainbow", "command": {"type": "pattern", "name": "rainbow", "params": {"speed": 500}}, "duration": 3000},
                    {"id": "flash2", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#00FFFF", "speed": 200}}, "duration": 500},
                    {"id": "sparkle", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#FFD700", "bgColor": "#FF1493", "speed": 50, "density": 0.3}}, "duration": 3000},
                    {"id": "flash3", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFF00", "speed": 200}}, "duration": 500},
                    {"id": "wave", "command": {"type": "pattern", "name": "wave", "params": {"color": "#FF4444", "color2": "#4444FF", "speed": 800}}, "duration": 3000},
                ],
                "loop": {"count": 0, "start_step": "flash1", "end_step": "wave"}
            }
        }
    },
    {
        "id": 16, "category": "multi_step", "prompt": "simulate rain and thunder",
        "program": {
            "program": {
                "name": "Rain & Thunder",
                "steps": [
                    {"id": "rain", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#6688CC", "bgColor": "#0a0a1a", "speed": 60, "density": 0.15}}, "duration": 5000},
                    {"id": "lightning", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 150}}, "duration": 300},
                    {"id": "rumble", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#2a2a4a", "speed": 1000}}, "duration": 2000},
                    {"id": "heavy_rain", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#4466AA", "bgColor": "#050510", "speed": 40, "density": 0.25}}, "duration": 6000},
                    {"id": "flash", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#EEEEFF", "speed": 100}}, "duration": 200},
                    {"id": "calm", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#6688CC", "bgColor": "#0a0a1a", "speed": 80, "density": 0.1}}, "duration": 4000},
                ],
                "loop": {"count": 0, "start_step": "rain", "end_step": "calm"}
            }
        }
    },
    {
        "id": 17, "category": "multi_step", "prompt": "sleep timer that dims over 30 minutes",
        "program": {
            "program": {
                "name": "Sleep Timer",
                "steps": [
                    {"id": "warm", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#D88B70", "speed": 5000}}, "duration": 600000},
                    {"id": "dim1", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#8B5A3A", "speed": 6000}}, "duration": 600000},
                    {"id": "dim2", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#4A2D1A", "speed": 7000}}, "duration": 600000},
                    {"id": "off", "command": {"type": "pattern", "name": "solid", "params": {"color": "#000000"}}, "duration": None},
                ]
            }
        }
    },
    {
        "id": 18, "category": "multi_step", "prompt": "countdown from 5",
        "program": {
            "program": {
                "name": "Countdown",
                "steps": [
                    {"id": "five", "command": {"type": "render", "elements": [{"type": "fill", "color": "#0a0a2a"}, {"type": "text", "content": "5", "x": 4, "y": 4, "color": "#00FF88"}]}, "duration": 1000},
                    {"id": "four", "command": {"type": "render", "elements": [{"type": "fill", "color": "#0a0a2a"}, {"type": "text", "content": "4", "x": 4, "y": 4, "color": "#44FF44"}]}, "duration": 1000},
                    {"id": "three", "command": {"type": "render", "elements": [{"type": "fill", "color": "#0a0a2a"}, {"type": "text", "content": "3", "x": 4, "y": 4, "color": "#FFFF00"}]}, "duration": 1000},
                    {"id": "two", "command": {"type": "render", "elements": [{"type": "fill", "color": "#0a0a2a"}, {"type": "text", "content": "2", "x": 4, "y": 4, "color": "#FF8800"}]}, "duration": 1000},
                    {"id": "one", "command": {"type": "render", "elements": [{"type": "fill", "color": "#0a0a2a"}, {"type": "text", "content": "1", "x": 4, "y": 4, "color": "#FF0000"}]}, "duration": 1000},
                    {"id": "go", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 300}}, "duration": 500},
                ],
                "on_complete": {"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 1000}}}
            }
        }
    },
    {
        "id": 19, "category": "multi_step", "prompt": "traffic light sequence",
        "program": {
            "program": {
                "name": "Traffic Light",
                "steps": [
                    {"id": "red", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "rect", "x": 3, "y": 1, "w": 4, "h": 12, "color": "#333333"},
                        {"type": "rect", "x": 4, "y": 2, "w": 2, "h": 2, "color": "#FF0000"},
                        {"type": "rect", "x": 4, "y": 5, "w": 2, "h": 2, "color": "#333300"},
                        {"type": "rect", "x": 4, "y": 8, "w": 2, "h": 2, "color": "#003300"},
                    ]}, "duration": 4000},
                    {"id": "yellow", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "rect", "x": 3, "y": 1, "w": 4, "h": 12, "color": "#333333"},
                        {"type": "rect", "x": 4, "y": 2, "w": 2, "h": 2, "color": "#330000"},
                        {"type": "rect", "x": 4, "y": 5, "w": 2, "h": 2, "color": "#FFFF00"},
                        {"type": "rect", "x": 4, "y": 8, "w": 2, "h": 2, "color": "#003300"},
                    ]}, "duration": 2000},
                    {"id": "green", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "rect", "x": 3, "y": 1, "w": 4, "h": 12, "color": "#333333"},
                        {"type": "rect", "x": 4, "y": 2, "w": 2, "h": 2, "color": "#330000"},
                        {"type": "rect", "x": 4, "y": 5, "w": 2, "h": 2, "color": "#333300"},
                        {"type": "rect", "x": 4, "y": 8, "w": 2, "h": 2, "color": "#00FF00"},
                    ]}, "duration": 4000},
                ],
                "loop": {"count": 0, "start_step": "red", "end_step": "green"}
            }
        }
    },
    {
        "id": 20, "category": "multi_step", "prompt": "romantic evening ambiance",
        "program": {
            "program": {
                "name": "Romantic Evening",
                "steps": [
                    {"id": "warm_glow", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#FFB6C1", "speed": 4000}}, "duration": 8000},
                    {"id": "deep_rose", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#9370DB", "color2": "#FFB6C1"}}, "duration": 8000},
                    {"id": "candlelight", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#FFD700", "bgColor": "#4a1020", "speed": 150, "density": 0.08}}, "duration": 8000},
                    {"id": "soft_wave", "command": {"type": "pattern", "name": "wave", "params": {"color": "#FF69B4", "color2": "#9370DB", "speed": 3000}}, "duration": 8000},
                ],
                "loop": {"count": 0, "start_step": "warm_glow", "end_step": "soft_wave"}
            }
        }
    },
    {
        "id": 21, "category": "multi_step", "prompt": "weather display showing sunny and 24 degrees",
        "program": {
            "program": {
                "name": "Weather Sunny 24°",
                "steps": [{
                    "id": "display",
                    "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#0a1a3a"},
                        # Sun icon top-left
                        {"type": "rect", "x": 1, "y": 2, "w": 3, "h": 3, "color": "#FFD700"},
                        {"type": "pixel", "x": 2, "y": 1, "color": "#FFA500"},
                        {"type": "pixel", "x": 0, "y": 3, "color": "#FFA500"},
                        {"type": "pixel", "x": 4, "y": 3, "color": "#FFA500"},
                        {"type": "pixel", "x": 2, "y": 5, "color": "#FFA500"},
                        # Temperature
                        {"type": "text", "content": "24", "x": 1, "y": 7, "color": "#FFFFFF"},
                        # Degree symbol
                        {"type": "pixel", "x": 8, "y": 7, "color": "#FFFFFF"},
                        # C for Celsius
                        {"type": "text", "content": "C", "x": 7, "y": 9, "color": "#87CEEB"},
                    ]},
                    "duration": None
                }]
            }
        }
    },
]


def send_program(program_data: dict) -> bool:
    try:
        data = json.dumps(program_data).encode("utf-8")
        req = urllib.request.Request(
            f"{LAMP_SERVER_URL}/program",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  SERVER ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Benchmark Claude Opus 4.6 on lamp prompts")
    parser.add_argument("--fast", action="store_true", help="2s pause instead of 5s")
    parser.add_argument("--index", type=int, help="Run a single test by index (1-21)")
    parser.add_argument("--category", choices=["pixel_art", "analog_clock", "multi_step"])
    args = parser.parse_args()

    pause = 2 if args.fast else 5
    tests = TEST_CASES

    if args.index:
        tests = [t for t in tests if t["id"] == args.index]
    elif args.category:
        tests = [t for t in tests if t["category"] == args.category]

    total = len(tests)
    print("=" * 60)
    print(f"  CLAUDE OPUS 4.6 BENCHMARK — {total} test cases")
    print(f"  Server: {LAMP_SERVER_URL}")
    print(f"  Pause between tests: {pause}s")
    print("=" * 60)
    print()

    results = []
    for i, test in enumerate(tests):
        idx = test["id"]
        cat = test["category"]
        prompt = test["prompt"]

        print(f"[{i+1:2d}/{total}] {cat:14s} | {prompt}")

        ok = send_program(test["program"])
        status = "OK" if ok else "FAIL"
        print(f"         -> {'SENT' if ok else 'SEND FAILED'}")
        results.append({"id": idx, "status": status, "prompt": prompt})

        if i < total - 1:
            print(f"         (waiting {pause}s — check emulator)")
            time.sleep(pause)

    print()
    print("=" * 60)
    print("  SUMMARY (Claude Opus 4.6)")
    print("=" * 60)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    for r in results:
        symbol = "OK" if r["status"] == "OK" else "FAIL"
        print(f"  [{r['id']:2d}] {symbol:4s} | {r['prompt']}")

    print()
    print(f"  {ok_count}/{total} successfully sent to server")


if __name__ == "__main__":
    main()

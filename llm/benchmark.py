"""
Benchmark: Claude-generated lamp programs for training data quality evaluation.

Tests whether Claude's output quality is good enough to use as synthetic
training data for fine-tuning the local 3B model.

21 test cases:
  #1-10:  Pixel art (render commands with shapes)
  #11:    Analog clock (render)
  #12-21: Multi-step ambiguous programs (patterns + render + loops)

Usage:
  python benchmark.py                  # Run all, send to server one by one
  python benchmark.py --dry-run        # Save to JSONL only, don't send
  python benchmark.py --index 5        # Run only test case #5
  python benchmark.py --fast           # 2s pause instead of 5s
  python benchmark.py --save-training  # Save all as training_data.jsonl
"""

import json
import time
import sys
import argparse
import urllib.request
import urllib.error

LAMP_SERVER_URL = "http://localhost:3001"

# =============================================================================
# TEST CASES: Each has a prompt (what the user would say) and the program
# Claude would generate. These are the "teacher" outputs.
# =============================================================================

TEST_CASES = [
    # =========================================================================
    # PIXEL ART (10) — render commands drawing shapes on the 10×14 grid
    # =========================================================================
    {
        "id": 1,
        "category": "pixel_art",
        "prompt": "show a star",
        "program": {
            "program": {
                "name": "Star",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a0a2a"},
                            {"type": "pixel", "x": 4, "y": 2, "color": "#FFD700"},
                            {"type": "pixel", "x": 3, "y": 3, "color": "#FFD700"},
                            {"type": "pixel", "x": 5, "y": 3, "color": "#FFD700"},
                            {"type": "pixel", "x": 2, "y": 4, "color": "#FFD700"},
                            {"type": "pixel", "x": 6, "y": 4, "color": "#FFD700"},
                            {"type": "rect", "x": 0, "y": 5, "w": 9, "h": 1, "color": "#FFD700"},
                            {"type": "pixel", "x": 2, "y": 6, "color": "#FFD700"},
                            {"type": "pixel", "x": 4, "y": 6, "color": "#FFD700"},
                            {"type": "pixel", "x": 6, "y": 6, "color": "#FFD700"},
                            {"type": "pixel", "x": 1, "y": 7, "color": "#FFD700"},
                            {"type": "pixel", "x": 3, "y": 7, "color": "#FFD700"},
                            {"type": "pixel", "x": 5, "y": 7, "color": "#FFD700"},
                            {"type": "pixel", "x": 7, "y": 7, "color": "#FFD700"},
                            {"type": "pixel", "x": 0, "y": 8, "color": "#FFD700"},
                            {"type": "pixel", "x": 8, "y": 8, "color": "#FFD700"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 2,
        "category": "pixel_art",
        "prompt": "draw a smiley face",
        "program": {
            "program": {
                "name": "Smiley",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#1a1a1a"},
                            # Yellow circle (rects approximating a circle)
                            {"type": "rect", "x": 3, "y": 2, "w": 4, "h": 1, "color": "#FFD700"},
                            {"type": "rect", "x": 2, "y": 3, "w": 6, "h": 1, "color": "#FFD700"},
                            {"type": "rect", "x": 1, "y": 4, "w": 8, "h": 5, "color": "#FFD700"},
                            {"type": "rect", "x": 2, "y": 9, "w": 6, "h": 1, "color": "#FFD700"},
                            {"type": "rect", "x": 3, "y": 10, "w": 4, "h": 1, "color": "#FFD700"},
                            # Eyes (dark)
                            {"type": "pixel", "x": 3, "y": 5, "color": "#1a1a1a"},
                            {"type": "pixel", "x": 6, "y": 5, "color": "#1a1a1a"},
                            # Smile (dark curve)
                            {"type": "pixel", "x": 3, "y": 7, "color": "#1a1a1a"},
                            {"type": "rect", "x": 4, "y": 8, "w": 2, "h": 1, "color": "#1a1a1a"},
                            {"type": "pixel", "x": 6, "y": 7, "color": "#1a1a1a"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 3,
        "category": "pixel_art",
        "prompt": "show an arrow pointing up",
        "program": {
            "program": {
                "name": "Up Arrow",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a1a0a"},
                            # Arrow head (triangle)
                            {"type": "pixel", "x": 4, "y": 1, "color": "#00FF44"},
                            {"type": "rect", "x": 3, "y": 2, "w": 3, "h": 1, "color": "#00FF44"},
                            {"type": "rect", "x": 2, "y": 3, "w": 5, "h": 1, "color": "#00FF44"},
                            {"type": "rect", "x": 1, "y": 4, "w": 7, "h": 1, "color": "#00FF44"},
                            # Shaft
                            {"type": "rect", "x": 3, "y": 5, "w": 3, "h": 6, "color": "#00FF44"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 4,
        "category": "pixel_art",
        "prompt": "draw a house",
        "program": {
            "program": {
                "name": "House",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a1a2a"},
                            # Roof (red triangle)
                            {"type": "pixel", "x": 4, "y": 1, "color": "#CC4444"},
                            {"type": "rect", "x": 3, "y": 2, "w": 3, "h": 1, "color": "#CC4444"},
                            {"type": "rect", "x": 2, "y": 3, "w": 5, "h": 1, "color": "#CC4444"},
                            {"type": "rect", "x": 1, "y": 4, "w": 7, "h": 1, "color": "#CC4444"},
                            # Walls (tan)
                            {"type": "rect", "x": 1, "y": 5, "w": 7, "h": 7, "color": "#DEB887"},
                            # Door (brown)
                            {"type": "rect", "x": 4, "y": 9, "w": 2, "h": 3, "color": "#8B4513"},
                            # Windows (blue)
                            {"type": "rect", "x": 2, "y": 6, "w": 2, "h": 2, "color": "#87CEEB"},
                            {"type": "rect", "x": 6, "y": 6, "w": 1, "h": 2, "color": "#87CEEB"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 5,
        "category": "pixel_art",
        "prompt": "show a music note",
        "program": {
            "program": {
                "name": "Music Note",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#1a0a2a"},
                            # Note head (filled oval at bottom)
                            {"type": "rect", "x": 2, "y": 8, "w": 3, "h": 2, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 1, "y": 9, "color": "#FFFFFF"},
                            # Stem (vertical line going up)
                            {"type": "rect", "x": 4, "y": 2, "w": 1, "h": 7, "color": "#FFFFFF"},
                            # Flag (curves to the right)
                            {"type": "pixel", "x": 5, "y": 2, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 6, "y": 3, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 6, "y": 4, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 5, "y": 5, "color": "#FFFFFF"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 6,
        "category": "pixel_art",
        "prompt": "draw a cat face",
        "program": {
            "program": {
                "name": "Cat Face",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#1a1a1a"},
                            # Ears (pointed triangles)
                            {"type": "pixel", "x": 1, "y": 1, "color": "#FF8C00"},
                            {"type": "pixel", "x": 8, "y": 1, "color": "#FF8C00"},
                            {"type": "rect", "x": 1, "y": 2, "w": 2, "h": 1, "color": "#FF8C00"},
                            {"type": "rect", "x": 7, "y": 2, "w": 2, "h": 1, "color": "#FF8C00"},
                            # Face (orange filled area)
                            {"type": "rect", "x": 1, "y": 3, "w": 8, "h": 6, "color": "#FF8C00"},
                            {"type": "rect", "x": 2, "y": 9, "w": 6, "h": 1, "color": "#FF8C00"},
                            # Eyes (green cat eyes)
                            {"type": "pixel", "x": 3, "y": 4, "color": "#00FF00"},
                            {"type": "pixel", "x": 6, "y": 4, "color": "#00FF00"},
                            # Nose (pink)
                            {"type": "pixel", "x": 4, "y": 6, "color": "#FF69B4"},
                            {"type": "pixel", "x": 5, "y": 6, "color": "#FF69B4"},
                            # Mouth
                            {"type": "pixel", "x": 3, "y": 7, "color": "#CC6600"},
                            {"type": "pixel", "x": 6, "y": 7, "color": "#CC6600"},
                            # Whiskers (extend beyond face)
                            {"type": "pixel", "x": 0, "y": 5, "color": "#CCCCCC"},
                            {"type": "pixel", "x": 0, "y": 6, "color": "#CCCCCC"},
                            {"type": "pixel", "x": 9, "y": 5, "color": "#CCCCCC"},
                            {"type": "pixel", "x": 9, "y": 6, "color": "#CCCCCC"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 7,
        "category": "pixel_art",
        "prompt": "show a sun",
        "program": {
            "program": {
                "name": "Sun",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a1a2a"},
                            # Rays (before body so body draws on top)
                            {"type": "pixel", "x": 4, "y": 1, "color": "#FFA500"},
                            {"type": "pixel", "x": 1, "y": 2, "color": "#FFA500"},
                            {"type": "pixel", "x": 7, "y": 2, "color": "#FFA500"},
                            {"type": "pixel", "x": 0, "y": 5, "color": "#FFA500"},
                            {"type": "pixel", "x": 8, "y": 5, "color": "#FFA500"},
                            {"type": "pixel", "x": 1, "y": 8, "color": "#FFA500"},
                            {"type": "pixel", "x": 7, "y": 8, "color": "#FFA500"},
                            {"type": "pixel", "x": 4, "y": 9, "color": "#FFA500"},
                            # Sun body (circle approx)
                            {"type": "rect", "x": 3, "y": 3, "w": 3, "h": 1, "color": "#FFD700"},
                            {"type": "rect", "x": 2, "y": 4, "w": 5, "h": 3, "color": "#FFD700"},
                            {"type": "rect", "x": 3, "y": 7, "w": 3, "h": 1, "color": "#FFD700"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 8,
        "category": "pixel_art",
        "prompt": "draw a tree",
        "program": {
            "program": {
                "name": "Tree",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a1a0a"},
                            # Tree canopy (tiered triangle)
                            {"type": "pixel", "x": 4, "y": 1, "color": "#228B22"},
                            {"type": "rect", "x": 3, "y": 2, "w": 3, "h": 1, "color": "#228B22"},
                            {"type": "rect", "x": 2, "y": 3, "w": 5, "h": 1, "color": "#228B22"},
                            {"type": "rect", "x": 1, "y": 4, "w": 7, "h": 1, "color": "#228B22"},
                            {"type": "rect", "x": 2, "y": 5, "w": 5, "h": 1, "color": "#2E8B57"},
                            {"type": "rect", "x": 1, "y": 6, "w": 7, "h": 1, "color": "#2E8B57"},
                            {"type": "rect", "x": 0, "y": 7, "w": 9, "h": 1, "color": "#2E8B57"},
                            # Trunk (brown)
                            {"type": "rect", "x": 4, "y": 8, "w": 1, "h": 3, "color": "#8B4513"},
                            # Ground
                            {"type": "rect", "x": 0, "y": 12, "w": 10, "h": 2, "color": "#654321"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 9,
        "category": "pixel_art",
        "prompt": "show a lightning bolt",
        "program": {
            "program": {
                "name": "Lightning",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a0a2a"},
                            # Lightning bolt (zigzag shape)
                            {"type": "rect", "x": 4, "y": 1, "w": 3, "h": 1, "color": "#FFFF00"},
                            {"type": "rect", "x": 3, "y": 2, "w": 3, "h": 1, "color": "#FFFF00"},
                            {"type": "rect", "x": 2, "y": 3, "w": 5, "h": 1, "color": "#FFD700"},
                            {"type": "rect", "x": 4, "y": 4, "w": 3, "h": 1, "color": "#FFFF00"},
                            {"type": "rect", "x": 3, "y": 5, "w": 3, "h": 1, "color": "#FFFF00"},
                            {"type": "rect", "x": 2, "y": 6, "w": 3, "h": 1, "color": "#FFD700"},
                            {"type": "pixel", "x": 3, "y": 7, "color": "#FFD700"},
                            {"type": "pixel", "x": 2, "y": 8, "color": "#FFD700"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
    {
        "id": 10,
        "category": "pixel_art",
        "prompt": "draw a skull",
        "program": {
            "program": {
                "name": "Skull",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#1a0a0a"},
                            # Cranium (rounded top)
                            {"type": "rect", "x": 3, "y": 1, "w": 4, "h": 1, "color": "#EEEEEE"},
                            {"type": "rect", "x": 2, "y": 2, "w": 6, "h": 1, "color": "#EEEEEE"},
                            {"type": "rect", "x": 1, "y": 3, "w": 8, "h": 3, "color": "#EEEEEE"},
                            # Eye sockets (dark holes)
                            {"type": "rect", "x": 2, "y": 3, "w": 2, "h": 2, "color": "#1a0a0a"},
                            {"type": "rect", "x": 6, "y": 3, "w": 2, "h": 2, "color": "#1a0a0a"},
                            # Nose
                            {"type": "pixel", "x": 4, "y": 5, "color": "#1a0a0a"},
                            {"type": "pixel", "x": 5, "y": 5, "color": "#1a0a0a"},
                            # Jaw
                            {"type": "rect", "x": 2, "y": 6, "w": 6, "h": 2, "color": "#DDDDDD"},
                            # Teeth (dark gaps)
                            {"type": "pixel", "x": 3, "y": 7, "color": "#1a0a0a"},
                            {"type": "pixel", "x": 5, "y": 7, "color": "#1a0a0a"},
                            {"type": "pixel", "x": 7, "y": 7, "color": "#1a0a0a"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },

    # =========================================================================
    # ANALOG CLOCK (1)
    # =========================================================================
    {
        "id": 11,
        "category": "analog_clock",
        "prompt": "show an analog clock at 3 o'clock",
        "program": {
            "program": {
                "name": "Analog Clock 3:00",
                "steps": [{
                    "id": "show",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a0a1a"},
                            # Clock face (circle approximated with rects)
                            {"type": "rect", "x": 3, "y": 1, "w": 4, "h": 1, "color": "#222233"},
                            {"type": "rect", "x": 2, "y": 2, "w": 6, "h": 1, "color": "#222233"},
                            {"type": "rect", "x": 1, "y": 3, "w": 8, "h": 5, "color": "#222233"},
                            {"type": "rect", "x": 2, "y": 8, "w": 6, "h": 1, "color": "#222233"},
                            {"type": "rect", "x": 3, "y": 9, "w": 4, "h": 1, "color": "#222233"},
                            # Hour markers (12, 3, 6, 9)
                            {"type": "pixel", "x": 4, "y": 2, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 7, "y": 5, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 4, "y": 8, "color": "#FFFFFF"},
                            {"type": "pixel", "x": 1, "y": 5, "color": "#FFFFFF"},
                            # Center dot
                            {"type": "pixel", "x": 4, "y": 5, "color": "#FF0000"},
                            # Minute hand → 12 (straight up)
                            {"type": "pixel", "x": 4, "y": 4, "color": "#CCCCCC"},
                            {"type": "pixel", "x": 4, "y": 3, "color": "#CCCCCC"},
                            # Hour hand → 3 (right)
                            {"type": "pixel", "x": 5, "y": 5, "color": "#CCCCCC"},
                            {"type": "pixel", "x": 6, "y": 5, "color": "#CCCCCC"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },

    # =========================================================================
    # MULTI-STEP AMBIGUOUS PROGRAMS (10)
    # =========================================================================
    {
        "id": 12,
        "category": "multi_step",
        "prompt": "be a pomodoro timer",
        "program": {
            "program": {
                "name": "Pomodoro",
                "steps": [
                    {
                        "id": "work",
                        "command": {
                            "type": "render",
                            "elements": [
                                {"type": "fill", "color": "#2a0000"},
                                {"type": "text", "content": "25", "x": 2, "y": 4, "color": "#FF3333"},
                                {"type": "rect", "x": 0, "y": 12, "w": 10, "h": 2, "color": "#FF3333"},
                            ]
                        },
                        "duration": 1500000
                    },
                    {
                        "id": "work_end",
                        "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 500}},
                        "duration": 2000
                    },
                    {
                        "id": "break",
                        "command": {
                            "type": "render",
                            "elements": [
                                {"type": "fill", "color": "#002a00"},
                                {"type": "text", "content": "05", "x": 2, "y": 4, "color": "#33FF33"},
                                {"type": "rect", "x": 0, "y": 12, "w": 10, "h": 2, "color": "#33FF33"},
                            ]
                        },
                        "duration": 300000
                    },
                    {
                        "id": "break_end",
                        "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFD700", "speed": 300}},
                        "duration": 2000
                    },
                ],
                "loop": {"count": 4, "start_step": "work", "end_step": "break_end"},
                "on_complete": {"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 2000}}}
            }
        }
    },
    {
        "id": 13,
        "category": "multi_step",
        "prompt": "simulate a sunrise",
        "program": {
            "program": {
                "name": "Sunrise",
                "steps": [
                    {"id": "night", "command": {"type": "pattern", "name": "solid", "params": {"color": "#050510"}}, "duration": 5000},
                    {"id": "predawn", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#191970", "color2": "#1a0a0a"}}, "duration": 8000},
                    {"id": "dawn", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#FF6B4A", "color2": "#483D8B"}}, "duration": 10000},
                    {"id": "sunrise", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#FFD700", "color2": "#FF6B4A"}}, "duration": 10000},
                    {"id": "morning", "command": {"type": "pattern", "name": "gradient", "params": {"color": "#FFE4C4", "color2": "#87CEEB"}}, "duration": None},
                ]
            }
        }
    },
    {
        "id": 14,
        "category": "multi_step",
        "prompt": "create a meditation session",
        "program": {
            "program": {
                "name": "Meditation",
                "steps": [
                    {"id": "settle", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#4A90D9", "speed": 4000}}, "duration": 30000},
                    {"id": "deep", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#008B8B", "speed": 5000}}, "duration": 300000},
                    {"id": "emerge", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#E6E6FA", "speed": 3000}}, "duration": 30000},
                    {"id": "bell", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFD700", "speed": 1000}}, "duration": 3000},
                ],
                "on_complete": {"command": {"type": "pattern", "name": "gradient", "params": {"color": "#FFE4C4", "color2": "#F0F8FF"}}}
            }
        }
    },
    {
        "id": 15,
        "category": "multi_step",
        "prompt": "party mode",
        "program": {
            "program": {
                "name": "Party Mode",
                "steps": [
                    {"id": "strobe_r", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FF0000", "speed": 200}}, "duration": 500},
                    {"id": "strobe_b", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#0000FF", "speed": 200}}, "duration": 500},
                    {"id": "strobe_g", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#00FF00", "speed": 200}}, "duration": 500},
                    {"id": "rainbow", "command": {"type": "pattern", "name": "rainbow", "params": {"speed": 500}}, "duration": 5000},
                    {"id": "sparkle", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#FF00FF", "bgColor": "#000033", "speed": 50, "density": 0.2}}, "duration": 5000},
                ],
                "loop": {"count": 0, "start_step": "strobe_r", "end_step": "sparkle"}
            }
        }
    },
    {
        "id": 16,
        "category": "multi_step",
        "prompt": "simulate rain and thunder",
        "program": {
            "program": {
                "name": "Rain Storm",
                "steps": [
                    {"id": "drizzle", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#4466AA", "bgColor": "#0a0a1a", "speed": 100, "density": 0.06}}, "duration": 6000},
                    {"id": "buildup", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#6688CC", "bgColor": "#0a0a2a", "speed": 60, "density": 0.12}}, "duration": 4000},
                    {"id": "flash", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 150}}, "duration": 300},
                    {"id": "rumble", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#1a1a3a", "speed": 1500}}, "duration": 3000},
                    {"id": "downpour", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#8899DD", "bgColor": "#0a0a2a", "speed": 40, "density": 0.18}}, "duration": 5000},
                ],
                "loop": {"count": 0, "start_step": "drizzle", "end_step": "downpour"}
            }
        }
    },
    {
        "id": 17,
        "category": "multi_step",
        "prompt": "sleep timer that dims over 30 minutes",
        "program": {
            "program": {
                "name": "Sleep Timer",
                "steps": [
                    {"id": "warm", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#FFE4C4", "speed": 4000}}, "duration": 600000},
                    {"id": "dim", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#8B6C5C", "speed": 5000}}, "duration": 600000},
                    {"id": "fading", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#2a1a1a", "speed": 6000}}, "duration": 600000},
                ],
                "on_complete": {"command": {"type": "pattern", "name": "solid", "params": {"color": "#000000"}}}
            }
        }
    },
    {
        "id": 18,
        "category": "multi_step",
        "prompt": "countdown from 5",
        "program": {
            "program": {
                "name": "Countdown",
                "steps": [
                    {"id": "five", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "text", "content": "5", "x": 3, "y": 4, "color": "#00FF44"},
                    ]}, "duration": 1000},
                    {"id": "four", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "text", "content": "4", "x": 3, "y": 4, "color": "#66FF00"},
                    ]}, "duration": 1000},
                    {"id": "three", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "text", "content": "3", "x": 3, "y": 4, "color": "#FFFF00"},
                    ]}, "duration": 1000},
                    {"id": "two", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "text", "content": "2", "x": 3, "y": 4, "color": "#FF8800"},
                    ]}, "duration": 1000},
                    {"id": "one", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#1a1a1a"},
                        {"type": "text", "content": "1", "x": 3, "y": 4, "color": "#FF0000"},
                    ]}, "duration": 1000},
                    {"id": "go", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#003300"},
                        {"type": "text", "content": "GO", "x": 2, "y": 4, "color": "#00FF00"},
                    ]}, "duration": 3000},
                ],
                "on_complete": {"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 1000}}}
            }
        }
    },
    {
        "id": 19,
        "category": "multi_step",
        "prompt": "traffic light sequence",
        "program": {
            "program": {
                "name": "Traffic Light",
                "steps": [
                    {"id": "red", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#111111"},
                        {"type": "rect", "x": 3, "y": 0, "w": 4, "h": 13, "color": "#222222"},
                        {"type": "rect", "x": 4, "y": 1, "w": 2, "h": 2, "color": "#FF0000"},
                        {"type": "rect", "x": 4, "y": 5, "w": 2, "h": 2, "color": "#332200"},
                        {"type": "rect", "x": 4, "y": 9, "w": 2, "h": 2, "color": "#003300"},
                    ]}, "duration": 5000},
                    {"id": "yellow", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#111111"},
                        {"type": "rect", "x": 3, "y": 0, "w": 4, "h": 13, "color": "#222222"},
                        {"type": "rect", "x": 4, "y": 1, "w": 2, "h": 2, "color": "#330000"},
                        {"type": "rect", "x": 4, "y": 5, "w": 2, "h": 2, "color": "#FFFF00"},
                        {"type": "rect", "x": 4, "y": 9, "w": 2, "h": 2, "color": "#003300"},
                    ]}, "duration": 2000},
                    {"id": "green", "command": {"type": "render", "elements": [
                        {"type": "fill", "color": "#111111"},
                        {"type": "rect", "x": 3, "y": 0, "w": 4, "h": 13, "color": "#222222"},
                        {"type": "rect", "x": 4, "y": 1, "w": 2, "h": 2, "color": "#330000"},
                        {"type": "rect", "x": 4, "y": 5, "w": 2, "h": 2, "color": "#332200"},
                        {"type": "rect", "x": 4, "y": 9, "w": 2, "h": 2, "color": "#00FF00"},
                    ]}, "duration": 5000},
                ],
                "loop": {"count": 0, "start_step": "red", "end_step": "green"}
            }
        }
    },
    {
        "id": 20,
        "category": "multi_step",
        "prompt": "romantic evening ambiance",
        "program": {
            "program": {
                "name": "Romantic Evening",
                "steps": [
                    {
                        "id": "heart",
                        "command": {
                            "type": "render",
                            "elements": [
                                {"type": "fill", "color": "#1a0a1a"},
                                {"type": "pixel", "x": 3, "y": 3, "color": "#FF2266"},
                                {"type": "pixel", "x": 6, "y": 3, "color": "#FF2266"},
                                {"type": "rect", "x": 2, "y": 4, "w": 3, "h": 2, "color": "#FF2266"},
                                {"type": "rect", "x": 5, "y": 4, "w": 3, "h": 2, "color": "#FF2266"},
                                {"type": "rect", "x": 3, "y": 6, "w": 4, "h": 2, "color": "#FF2266"},
                                {"type": "rect", "x": 4, "y": 8, "w": 2, "h": 1, "color": "#FF2266"},
                            ]
                        },
                        "duration": 5000
                    },
                    {"id": "glow", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#FF69B4", "speed": 4000}}, "duration": 15000},
                    {"id": "twinkle", "command": {"type": "pattern", "name": "sparkle", "params": {"color": "#FFB6C1", "bgColor": "#1a0a1a", "speed": 150, "density": 0.06}}, "duration": 10000},
                    {"id": "waves", "command": {"type": "pattern", "name": "wave", "params": {"color": "#9370DB", "color2": "#FF69B4", "speed": 3000}}, "duration": 15000},
                ],
                "loop": {"count": 0, "start_step": "heart", "end_step": "waves"}
            }
        }
    },
    {
        "id": 21,
        "category": "multi_step",
        "prompt": "weather display showing sunny and 24 degrees",
        "program": {
            "program": {
                "name": "Weather Sunny 24C",
                "steps": [{
                    "id": "display",
                    "command": {
                        "type": "render",
                        "elements": [
                            {"type": "fill", "color": "#0a1a2a"},
                            # Sun icon (top section)
                            {"type": "pixel", "x": 4, "y": 0, "color": "#FFA500"},
                            {"type": "pixel", "x": 1, "y": 1, "color": "#FFA500"},
                            {"type": "pixel", "x": 7, "y": 1, "color": "#FFA500"},
                            {"type": "rect", "x": 3, "y": 1, "w": 3, "h": 1, "color": "#FFD700"},
                            {"type": "rect", "x": 2, "y": 2, "w": 5, "h": 2, "color": "#FFD700"},
                            {"type": "rect", "x": 3, "y": 4, "w": 3, "h": 1, "color": "#FFD700"},
                            {"type": "pixel", "x": 0, "y": 3, "color": "#FFA500"},
                            {"type": "pixel", "x": 8, "y": 3, "color": "#FFA500"},
                            # Divider
                            {"type": "line", "x1": 0, "y1": 6, "x2": 9, "y2": 6, "color": "#333333"},
                            # Temperature "24"
                            {"type": "text", "content": "24", "x": 2, "y": 8, "color": "#FFFFFF"},
                            # Degree dot
                            {"type": "pixel", "x": 9, "y": 8, "color": "#FFFFFF"},
                        ]
                    },
                    "duration": None
                }]
            }
        }
    },
]


# =============================================================================
# BENCHMARK RUNNER
# =============================================================================

def send_program(program_data: dict) -> bool:
    """Send a program to the lamp server."""
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
    except urllib.error.URLError:
        print("  ERROR: Cannot connect to server at", LAMP_SERVER_URL)
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def save_training_data(filepath: str = "training_data.jsonl"):
    """Save all test cases as JSONL training data."""
    with open(filepath, "w") as f:
        for tc in TEST_CASES:
            entry = {
                "prompt": tc["prompt"],
                "response": json.dumps(tc["program"], separators=(",", ":")),
            }
            f.write(json.dumps(entry) + "\n")
    print(f"Saved {len(TEST_CASES)} training examples to {filepath}")


def run_benchmark(indices=None, pause=5, dry_run=False):
    """Run benchmark, sending programs to the server for visual verification."""
    cases = TEST_CASES if indices is None else [tc for tc in TEST_CASES if tc["id"] in indices]

    print(f"\n{'='*60}")
    print(f"  LAMP PROGRAM BENCHMARK — {len(cases)} test cases")
    print(f"  Server: {LAMP_SERVER_URL}")
    print(f"  Pause between tests: {pause}s")
    print(f"{'='*60}\n")

    results = []
    for i, tc in enumerate(cases):
        print(f"[{tc['id']:2d}/{len(TEST_CASES)}] {tc['category']:14s} | {tc['prompt']}")

        if not dry_run:
            ok = send_program(tc["program"])
            status = "SENT" if ok else "FAIL"
            print(f"         -> {status}")
            results.append({"id": tc["id"], "prompt": tc["prompt"], "sent": ok})

            if i < len(cases) - 1:
                print(f"         (waiting {pause}s — check emulator)")
                time.sleep(pause)
        else:
            program_json = json.dumps(tc["program"], separators=(",", ":"))
            print(f"         -> {len(program_json)} chars JSON")
            results.append({"id": tc["id"], "prompt": tc["prompt"], "chars": len(program_json)})

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "OK" if r.get("sent", True) else "FAIL"
        print(f"  [{r['id']:2d}] {status:4s} | {r['prompt']}")

    if not dry_run:
        sent = sum(1 for r in results if r.get("sent"))
        print(f"\n  {sent}/{len(results)} successfully sent to server")
    print()


def main():
    parser = argparse.ArgumentParser(description="Lamp program benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to server")
    parser.add_argument("--index", type=int, nargs="+", help="Run specific test case(s) by ID")
    parser.add_argument("--fast", action="store_true", help="2s pause instead of 5s")
    parser.add_argument("--save-training", action="store_true", help="Save as training_data.jsonl")
    parser.add_argument("--category", choices=["pixel_art", "analog_clock", "multi_step"], help="Run only one category")
    args = parser.parse_args()

    if args.save_training:
        save_training_data()
        return

    indices = args.index
    if args.category:
        indices = [tc["id"] for tc in TEST_CASES if tc["category"] == args.category]

    pause = 2 if args.fast else 5
    run_benchmark(indices=indices, pause=pause, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

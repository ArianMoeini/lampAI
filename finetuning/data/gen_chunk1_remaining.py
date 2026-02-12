#!/usr/bin/env python3
"""Generate lamp program responses for remaining render_diverse prompts in chunk 1."""

import json
import hashlib

def prompt_hash(prompt):
    return int(hashlib.md5(prompt.encode()).hexdigest(), 16)

def make_render_program(name, elements, duration=None):
    """Create a simple render program with one step."""
    return json.dumps({
        "program": {
            "name": name,
            "steps": [{"id": "show", "command": {"type": "render", "elements": elements}, "duration": duration}]
        }
    }, separators=(',', ':'))

def make_multi_step_render(name, steps, loop=None):
    """Create a multi-step render program."""
    prog = {"program": {"name": name, "steps": steps}}
    if loop:
        prog["program"]["loop"] = loop
    return json.dumps(prog, separators=(',', ':'))

def make_mixed_program(name, steps, loop=None, on_complete=None):
    """Create a mixed render+pattern program."""
    prog = {"program": {"name": name, "steps": steps}}
    if loop:
        prog["program"]["loop"] = loop
    if on_complete:
        prog["program"]["on_complete"] = on_complete
    return json.dumps(prog, separators=(',', ':'))

def fill(color):
    return {"type": "fill", "color": color}

def px(x, y, color):
    return {"type": "pixel", "x": x, "y": y, "color": color}

def rect(x, y, w, h, color):
    return {"type": "rect", "x": x, "y": y, "w": w, "h": h, "color": color}

def line(x1, y1, x2, y2, color):
    return {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color}

def text(content, x, y, color):
    return {"type": "text", "content": content, "x": x, "y": y, "color": color}

# ============================================================
# PIXEL ART DEFINITIONS
# Each returns (name, [elements])
# ============================================================

# --- NATURE: TREES ---
def art_pine_tree(prompt, bg="#0a0a2e"):
    h = prompt_hash(prompt)
    trunk = "#8B4513" if h % 2 == 0 else "#6B3410"
    green = "#228B22" if h % 3 != 0 else "#2E8B57"
    return "Pine Tree", [fill(bg), px(4,3,green), px(5,3,green), rect(3,4,4,2,green), rect(2,6,6,2,green), rect(4,8,2,3,trunk)]

def art_oak_tree(prompt, bg="#87CEEB"):
    return "Oak Tree", [fill(bg), rect(4,8,2,4,"#8B4513"), rect(2,3,6,5,"#228B22"), px(3,2,"#228B22"), px(6,2,"#228B22"), rect(0,12,10,2,"#8B4513")]

def art_palm_tree(prompt, bg="#FF8C00"):
    return "Palm Tree", [fill(bg), rect(4,6,2,7,"#8B4513"), px(3,3,"#228B22"), px(2,2,"#228B22"), px(6,3,"#228B22"), px(7,2,"#228B22"), px(4,2,"#228B22"), px(5,2,"#228B22"), px(1,3,"#228B22"), px(8,3,"#228B22"), rect(0,13,10,1,"#FFD700")]

def art_willow(prompt, bg="#87CEEB"):
    return "Willow Tree", [fill(bg), rect(4,4,2,6,"#8B4513"), rect(3,2,4,3,"#228B22"), px(2,3,"#228B22"), px(7,3,"#228B22"), line(2,4,1,8,"#2E8B57"), line(7,4,8,8,"#2E8B57"), line(3,3,2,7,"#228B22"), line(6,3,7,7,"#228B22"), rect(0,12,10,2,"#228B22")]

def art_cherry_blossom(prompt, bg="#E6E6FA"):
    return "Cherry Blossom", [fill(bg), line(4,12,5,5,"#8B4513"), line(5,5,7,3,"#8B4513"), line(4,6,2,4,"#8B4513"), px(7,2,"#FFB6C1"), px(8,3,"#FFB6C1"), px(6,3,"#FF69B4"), px(2,3,"#FFB6C1"), px(1,4,"#FF69B4"), px(3,4,"#FFB6C1"), px(5,4,"#FF69B4"), px(4,5,"#FFB6C1")]

# --- NATURE: LANDSCAPE ---
def art_waterfall(prompt, bg="#0a0a2e"):
    return "Waterfall", [fill(bg), rect(0,0,4,12,"#666666"), rect(6,0,4,12,"#666666"), rect(4,0,2,2,"#666666"), rect(4,2,2,10,"#4A90D9"), px(4,3,"#ADD8E6"), px(5,5,"#ADD8E6"), px(4,7,"#ADD8E6"), px(5,9,"#ADD8E6"), rect(2,12,6,2,"#4A90D9"), px(3,12,"#ADD8E6")]

def art_mountain(prompt, bg="#0a0a2e"):
    return "Mountains", [fill(bg), px(1,1,"#FFFFFF"), px(8,0,"#FFFFFF"), px(5,9,"#6B4C8B"), px(4,10,"#6B4C8B"), px(6,10,"#6B4C8B"), rect(3,11,5,1,"#6B4C8B"), rect(2,12,7,2,"#6B4C8B"), px(2,8,"#557B5E"), px(1,9,"#557B5E"), px(3,9,"#557B5E"), rect(0,10,5,4,"#557B5E"), px(5,10,"#557B5E"), px(5,11,"#FFFFFF"), px(2,7,"#FFFFFF")]

def art_volcano(prompt, bg="#0a0a2e"):
    return "Volcano", [fill(bg), px(4,4,"#FF4400"), px(5,4,"#FF4400"), px(4,3,"#FF6600"), px(5,3,"#FFAA00"), rect(3,5,4,2,"#555555"), rect(2,7,6,2,"#444444"), rect(1,9,8,5,"#333333"), px(4,2,"#FF0000"), px(5,2,"#FFAA00")]

def art_sun(prompt, bg="#87CEEB"):
    return "Sun", [fill(bg), rect(3,4,4,4,"#FFD700"), px(5,2,"#FFAA00"), px(2,4,"#FFAA00"), px(7,5,"#FFAA00"), px(4,9,"#FFAA00"), px(2,3,"#FFAA00"), px(7,3,"#FFAA00"), px(2,8,"#FFAA00"), px(7,8,"#FFAA00")]

def art_sunset_scene(prompt, bg="#FF6B4A"):
    return "Sunset", [fill("#0a0a2e"), rect(0,8,10,6,"#1a3a6a"), rect(0,6,10,3,"#FF6B4A"), rect(0,5,10,2,"#FF8C00"), rect(0,4,10,1,"#FFD700"), rect(3,5,4,3,"#FFD700"), px(2,7,"#FFD700"), px(7,7,"#FFD700")]

def art_cloud_rain(prompt, bg="#87CEEB"):
    return "Rain Cloud", [fill(bg), rect(2,3,6,3,"#999999"), px(1,4,"#999999"), px(8,4,"#999999"), rect(3,2,4,1,"#AAAAAA"), px(3,7,"#4A90D9"), px(5,8,"#4A90D9"), px(7,7,"#4A90D9"), px(4,9,"#4A90D9"), px(6,10,"#4A90D9"), px(3,11,"#4A90D9")]

def art_rainbow(prompt, bg="#87CEEB"):
    return "Rainbow", [fill(bg), line(1,9,4,4,"#FF0000"), line(1,10,5,5,"#FF8800"), line(2,11,6,6,"#FFFF00"), line(3,12,7,7,"#00FF00"), line(4,13,8,8,"#0000FF"), line(5,5,8,8,"#0000FF"), line(4,4,8,7,"#00FF00"), line(5,5,9,8,"#FFFF00"), px(9,7,"#FF8800"), px(9,6,"#FF0000")]

def art_wave(prompt, bg="#0a0a2e"):
    return "Ocean Wave", [fill(bg), rect(0,10,10,4,"#006994"), rect(0,8,10,2,"#0088AA"), px(1,7,"#00AACC"), px(2,6,"#00BBDD"), px(3,5,"#ADD8E6"), px(4,5,"#FFFFFF"), px(5,6,"#ADD8E6"), px(6,7,"#00AACC"), px(7,8,"#0088AA"), px(8,7,"#00AACC"), px(3,4,"#ADD8E6")]

# --- NATURE: PLANTS ---
def art_lotus(prompt, bg="#006994"):
    return "Lotus", [fill(bg), rect(3,7,4,2,"#FF69B4"), px(2,7,"#FFB6C1"), px(7,7,"#FFB6C1"), px(4,6,"#FF69B4"), px(5,6,"#FF69B4"), px(3,6,"#FFB6C1"), px(6,6,"#FFB6C1"), px(4,5,"#FFB6C1"), px(5,5,"#FFB6C1"), rect(2,9,6,1,"#228B22"), rect(1,10,8,1,"#006400")]

def art_cactus(prompt, bg="#FFD700"):
    return "Cactus", [fill(bg), rect(4,4,2,8,"#228B22"), rect(2,6,2,2,"#228B22"), px(2,5,"#228B22"), rect(6,7,2,2,"#228B22"), px(7,6,"#228B22"), px(4,3,"#FF69B4"), px(5,3,"#FF1493"), rect(0,12,10,2,"#C2B280")]

def art_mushroom(prompt, bg="#0a0a2e"):
    return "Mushrooms", [fill(bg), rect(3,5,4,2,"#FF0000"), px(4,5,"#FFFFFF"), px(6,6,"#FFFFFF"), px(2,6,"#FF0000"), px(7,5,"#FF0000"), rect(4,7,2,4,"#F5DEB3"), px(7,8,"#FF4444"), px(8,8,"#FF4444"), px(8,9,"#F5DEB3"), rect(0,11,10,3,"#228B22")]

def art_bamboo(prompt, bg="#F0F8FF"):
    return "Bamboo", [fill(bg), rect(2,0,1,14,"#228B22"), rect(5,0,1,14,"#2E8B57"), rect(8,0,1,14,"#228B22"), px(3,2,"#228B22"), px(3,3,"#228B22"), px(6,5,"#2E8B57"), px(6,6,"#2E8B57"), px(9,3,"#228B22"), px(9,4,"#228B22"), px(2,4,"#1a6b1a"), px(5,7,"#1a6b5a"), px(8,6,"#1a6b1a")]

def art_acorn(prompt, bg="#87CEEB"):
    return "Acorn", [fill(bg), rect(3,4,4,2,"#8B6914"), px(4,3,"#8B6914"), px(5,3,"#8B6914"), px(4,2,"#8B4513"), rect(3,6,4,3,"#D2691E"), rect(4,9,2,1,"#D2691E"), px(3,9,"#B8860B")]

def art_pinecone(prompt, bg="#228B22"):
    return "Pinecone", [fill(bg), px(4,3,"#8B4513"), px(5,3,"#8B4513"), rect(3,4,4,2,"#A0522D"), rect(3,6,4,2,"#8B4513"), rect(4,8,2,2,"#A0522D"), px(4,2,"#228B22"), px(5,2,"#228B22")]

def art_coral(prompt, bg="#006994"):
    return "Coral", [fill(bg), rect(3,8,1,4,"#FF6B4A"), px(3,7,"#FF6B4A"), px(2,6,"#FF6B4A"), px(4,7,"#FF6B4A"), rect(6,7,1,5,"#FF8C00"), px(6,6,"#FF8C00"), px(7,6,"#FF8C00"), px(5,8,"#FF6B4A"), px(8,9,"#FFAA55"), px(8,10,"#FFAA55"), rect(0,12,10,2,"#C2B280")]

def art_seashell(prompt, bg="#C2B280"):
    return "Seashell", [fill(bg), rect(3,5,4,4,"#FFB6C1"), px(2,6,"#FFB6C1"), px(7,6,"#FFB6C1"), px(4,4,"#FFC0CB"), px(5,4,"#FFC0CB"), rect(4,9,2,1,"#FFB6C1"), line(4,5,4,8,"#FF69B4"), line(5,5,5,8,"#FF69B4")]

# --- FOOD ---
def art_apple(prompt, bg="#0a0a2e"):
    h = prompt_hash(prompt)
    color = "#FF0000" if h % 2 == 0 else "#00AA00"
    return "Apple", [fill(bg), rect(3,5,4,4,color), px(2,6,color), px(7,6,color), rect(4,3,2,2,color), px(4,2,"#228B22"), px(5,2,"#228B22"), px(5,1,"#8B4513")]

def art_banana(prompt, bg="#0a0a2e"):
    return "Banana", [fill(bg), px(5,3,"#8B6914"), px(5,4,"#FFD700"), px(4,5,"#FFD700"), px(4,6,"#FFD700"), px(4,7,"#FFD700"), px(4,8,"#FFD700"), px(5,9,"#FFD700"), px(6,9,"#FFD700"), px(3,6,"#FFEE00"), px(3,7,"#FFEE00")]

def art_pizza(prompt, bg="#0a0a2e"):
    return "Pizza", [fill(bg), px(5,2,"#FFD700"), px(4,3,"#FFD700"), px(6,3,"#FFD700"), rect(3,4,5,2,"#FFD700"), rect(2,6,7,2,"#FFD700"), rect(1,8,9,2,"#FFD700"), px(5,4,"#FF0000"), px(3,6,"#FF0000"), px(7,6,"#FF0000"), px(4,8,"#FF0000"), px(6,8,"#FF0000"), rect(1,10,9,1,"#D2691E")]

def art_ice_cream(prompt, bg="#0a0a2e"):
    return "Ice Cream", [fill(bg), rect(3,3,4,3,"#FFB6C1"), px(2,4,"#FFB6C1"), px(7,4,"#FFB6C1"), rect(3,2,4,1,"#FF69B4"), px(4,6,"#D2691E"), px(5,6,"#D2691E"), px(4,7,"#D2691E"), px(5,7,"#D2691E"), px(4,8,"#D2691E"), px(5,8,"#D2691E"), px(5,9,"#D2691E")]

def art_cupcake(prompt, bg="#0a0a2e"):
    return "Cupcake", [fill(bg), rect(3,4,4,2,"#FF69B4"), px(2,5,"#FFB6C1"), px(7,5,"#FFB6C1"), px(4,3,"#FF1493"), px(5,3,"#FF1493"), rect(3,6,4,4,"#D2691E"), px(2,7,"#8B4513"), px(7,7,"#8B4513"), px(4,2,"#FF0000")]

def art_coffee(prompt, bg="#0a0a2e"):
    return "Coffee Cup", [fill(bg), rect(3,5,4,5,"#D2691E"), rect(2,5,1,4,"#8B4513"), rect(7,5,1,4,"#8B4513"), rect(3,4,4,1,"#4A2F1A"), px(4,3,"#CCCCCC"), px(5,2,"#CCCCCC"), px(4,1,"#CCCCCC"), rect(3,10,4,1,"#8B4513"), px(7,6,"#D2691E"), px(8,7,"#D2691E"), px(7,8,"#D2691E")]

def art_wine_glass(prompt, bg="#0a0a2e"):
    return "Wine Glass", [fill(bg), rect(4,3,2,3,"#8B0000"), px(3,4,"#8B0000"), px(6,4,"#8B0000"), px(3,3,"#CCCCCC"), px(6,3,"#CCCCCC"), rect(4,6,2,4,"#CCCCCC"), rect(3,10,4,1,"#CCCCCC")]

def art_burger(prompt, bg="#0a0a2e"):
    return "Burger", [fill(bg), rect(2,4,6,1,"#D2691E"), rect(2,5,6,1,"#228B22"), rect(2,6,6,1,"#FF0000"), rect(2,7,6,1,"#FFD700"), rect(2,8,6,1,"#8B4513"), rect(2,9,6,1,"#D2691E"), px(1,5,"#D2691E"), px(8,5,"#D2691E"), px(3,3,"#D2691E"), px(6,3,"#D2691E")]

def art_donut(prompt, bg="#0a0a2e"):
    return "Donut", [fill(bg), rect(3,4,4,1,"#FF69B4"), rect(2,5,6,4,"#FF69B4"), rect(3,9,4,1,"#FF69B4"), rect(4,6,2,2,"#0a0a2e"), px(3,6,"#D2691E"), px(6,6,"#D2691E"), px(3,7,"#D2691E"), px(6,7,"#D2691E"), px(4,4,"#FFD700"), px(6,5,"#00FF00"), px(3,5,"#FF0000")]

def art_watermelon(prompt, bg="#0a0a2e"):
    return "Watermelon", [fill(bg), rect(1,7,8,4,"#FF4444"), rect(1,6,8,1,"#FFFFFF"), rect(1,5,8,1,"#228B22"), px(3,8,"#000000"), px(5,9,"#000000"), px(7,8,"#000000"), px(2,9,"#000000"), px(6,8,"#000000")]

def art_cherry(prompt, bg="#0a0a2e"):
    return "Cherries", [fill(bg), rect(3,6,2,2,"#FF0000"), rect(6,7,2,2,"#FF0000"), px(3,5,"#CC0000"), px(6,6,"#CC0000"), line(4,5,5,3,"#228B22"), line(7,6,5,3,"#228B22"), px(5,2,"#228B22"), px(6,2,"#228B22")]

def art_grapes(prompt, bg="#0a0a2e"):
    return "Grapes", [fill(bg), px(4,3,"#8B008B"), px(5,3,"#8B008B"), px(3,4,"#9370DB"), px(4,4,"#8B008B"), px(5,4,"#9370DB"), px(6,4,"#8B008B"), px(4,5,"#9370DB"), px(5,5,"#8B008B"), px(3,5,"#8B008B"), px(6,5,"#9370DB"), px(4,6,"#8B008B"), px(5,6,"#9370DB"), px(5,7,"#8B008B"), px(4,2,"#228B22"), px(5,1,"#8B4513")]

def art_carrot(prompt, bg="#0a0a2e"):
    return "Carrot", [fill(bg), px(4,3,"#228B22"), px(5,3,"#228B22"), px(4,2,"#228B22"), rect(4,4,2,2,"#FF8C00"), rect(4,6,2,2,"#FF6B00"), px(4,8,"#FF6B00"), px(5,8,"#FF6B00"), px(5,9,"#FF5500"), px(5,10,"#FF4400")]

def art_corn(prompt, bg="#0a0a2e"):
    return "Corn", [fill(bg), px(4,2,"#228B22"), px(5,2,"#228B22"), px(3,3,"#228B22"), rect(4,3,2,1,"#FFD700"), rect(4,4,2,7,"#FFD700"), px(3,5,"#FFD700"), px(6,5,"#FFD700"), px(3,7,"#FFD700"), px(6,7,"#FFD700"), px(5,4,"#FFEE00"), px(4,6,"#FFEE00"), px(5,8,"#FFEE00")]

def art_cookie(prompt, bg="#0a0a2e"):
    return "Cookie", [fill(bg), rect(3,5,4,4,"#D2691E"), px(2,6,"#D2691E"), px(7,6,"#D2691E"), px(2,7,"#D2691E"), px(7,7,"#D2691E"), px(4,5,"#4A2F1A"), px(6,6,"#4A2F1A"), px(3,7,"#4A2F1A"), px(5,8,"#4A2F1A")]

def art_lollipop(prompt, bg="#0a0a2e"):
    return "Lollipop", [fill(bg), rect(3,3,4,4,"#FF69B4"), px(2,4,"#FF69B4"), px(7,4,"#FF69B4"), px(4,3,"#FF0000"), px(5,4,"#FFFF00"), px(4,5,"#00FF00"), px(5,6,"#4A90D9"), rect(4,7,2,5,"#D2691E")]

def art_popsicle(prompt, bg="#87CEEB"):
    return "Popsicle", [fill(bg), rect(3,3,4,4,"#FF4444"), rect(3,7,4,2,"#4A90D9"), rect(4,9,2,3,"#D2691E")]

def art_sushi(prompt, bg="#0a0a2e"):
    return "Sushi", [fill(bg), rect(2,5,6,4,"#FFFFFF"), rect(2,5,6,1,"#FF6347"), rect(3,4,4,1,"#FF6347"), rect(2,9,6,1,"#1a1a1a"), px(1,6,"#1a1a1a"), px(8,6,"#1a1a1a"), px(1,7,"#1a1a1a"), px(8,7,"#1a1a1a")]

def art_taco(prompt, bg="#0a0a2e"):
    return "Taco", [fill(bg), px(4,4,"#228B22"), px(5,4,"#228B22"), px(3,5,"#FF0000"), px(6,5,"#FF0000"), rect(3,5,4,2,"#FFD700"), rect(2,7,6,2,"#D2691E"), px(1,8,"#D2691E"), px(8,8,"#D2691E")]

def art_pretzel(prompt, bg="#0a0a2e"):
    return "Pretzel", [fill(bg), px(3,4,"#D2691E"), px(6,4,"#D2691E"), px(2,5,"#D2691E"), px(7,5,"#D2691E"), px(2,6,"#D2691E"), px(7,6,"#D2691E"), px(3,7,"#D2691E"), px(6,7,"#D2691E"), px(4,7,"#D2691E"), px(5,7,"#D2691E"), px(4,8,"#D2691E"), px(5,8,"#D2691E"), px(3,5,"#D2691E"), px(6,5,"#D2691E"), px(5,5,"#FFAA00"), px(3,6,"#FFAA00")]

# --- TECH ---
def art_smartphone(prompt, bg="#0a0a2e"):
    return "Phone", [fill(bg), rect(3,2,4,10,"#333333"), rect(4,3,2,7,"#4A90D9"), px(4,11,"#666666"), px(5,11,"#666666")]

def art_laptop(prompt, bg="#0a0a2e"):
    return "Laptop", [fill(bg), rect(2,4,6,5,"#333333"), rect(3,5,4,3,"#4A90D9"), rect(1,9,8,1,"#555555"), rect(0,10,10,1,"#444444")]

def art_gamepad(prompt, bg="#0a0a2e"):
    return "Game Controller", [fill(bg), rect(2,5,6,4,"#555555"), px(1,6,"#555555"), px(1,7,"#555555"), px(8,6,"#555555"), px(8,7,"#555555"), px(3,6,"#333333"), px(3,7,"#333333"), px(4,6,"#333333"), px(6,6,"#FF0000"), px(7,7,"#4A90D9"), px(7,6,"#228B22")]

def art_headphones(prompt, bg="#0a0a2e"):
    return "Headphones", [fill(bg), rect(3,3,4,1,"#333333"), px(2,4,"#333333"), px(7,4,"#333333"), px(2,5,"#333333"), px(7,5,"#333333"), rect(1,6,2,3,"#555555"), rect(7,6,2,3,"#555555")]

def art_camera(prompt, bg="#0a0a2e"):
    return "Camera", [fill(bg), rect(2,5,6,5,"#444444"), rect(1,4,8,1,"#555555"), rect(4,6,2,2,"#4A90D9"), px(3,6,"#4A90D9"), px(6,7,"#4A90D9"), px(7,4,"#FF0000")]

def art_battery(prompt, bg="#0a0a2e"):
    return "Battery", [fill(bg), rect(2,5,6,5,"#228B22"), rect(1,5,1,5,"#666666"), rect(8,5,1,5,"#666666"), rect(8,7,1,2,"#666666"), px(3,6,"#00FF00"), px(4,6,"#00FF00"), px(5,6,"#00FF00")]

def art_power_button(prompt, bg="#0a0a2e"):
    return "Power", [fill(bg), px(4,2,"#00FF00"), px(5,2,"#00FF00"), px(4,3,"#00FF00"), px(5,3,"#00FF00"), px(2,4,"#00FF00"), px(7,4,"#00FF00"), px(2,5,"#00FF00"), px(7,5,"#00FF00"), px(2,6,"#00FF00"), px(7,6,"#00FF00"), px(3,7,"#00FF00"), px(6,7,"#00FF00"), px(4,8,"#00FF00"), px(5,8,"#00FF00")]

def art_play_pause(prompt, bg="#0a0a2e"):
    return "Play Pause", [fill(bg), px(2,4,"#00FF00"), px(2,5,"#00FF00"), px(2,6,"#00FF00"), px(2,7,"#00FF00"), px(2,8,"#00FF00"), px(3,5,"#00FF00"), px(3,6,"#00FF00"), px(3,7,"#00FF00"), px(4,6,"#00FF00"), rect(6,4,1,5,"#FFFFFF"), rect(8,4,1,5,"#FFFFFF")]

def art_microphone(prompt, bg="#0a0a2e"):
    return "Microphone", [fill(bg), rect(4,3,2,4,"#CCCCCC"), px(3,4,"#AAAAAA"), px(6,4,"#AAAAAA"), px(3,5,"#AAAAAA"), px(6,5,"#AAAAAA"), px(3,7,"#AAAAAA"), px(6,7,"#AAAAAA"), rect(4,7,2,3,"#999999"), rect(3,10,4,1,"#666666")]

def art_satellite(prompt, bg="#0a0a2e"):
    return "Satellite", [fill(bg), px(1,1,"#FFF"), px(8,0,"#FFF"), px(6,3,"#FFF"), rect(3,5,4,2,"#999999"), px(2,4,"#4A90D9"), px(7,4,"#4A90D9"), px(1,3,"#4A90D9"), px(8,3,"#4A90D9"), px(4,7,"#CCCCCC"), px(5,7,"#CCCCCC")]

def art_drone(prompt, bg="#87CEEB"):
    return "Drone", [fill(bg), rect(4,6,2,1,"#444444"), px(2,5,"#666666"), px(7,5,"#666666"), px(1,4,"#888888"), px(3,4,"#888888"), px(6,4,"#888888"), px(8,4,"#888888"), px(4,7,"#4A90D9"), px(5,7,"#4A90D9")]

def art_robot(prompt, bg="#0a0a2e"):
    return "Robot", [fill(bg), rect(3,2,4,3,"#CCCCCC"), px(4,3,"#00FF00"), px(5,3,"#00FF00"), px(4,4,"#FF0000"), rect(3,5,4,4,"#AAAAAA"), px(2,6,"#CCCCCC"), px(7,6,"#CCCCCC"), rect(3,9,2,2,"#888888"), rect(5,9,2,2,"#888888")]

def art_arcade(prompt, bg="#0a0a2e"):
    return "Arcade", [fill(bg), rect(2,2,6,10,"#333399"), rect(3,3,4,3,"#000000"), px(4,4,"#00FF00"), px(5,4,"#FF0000"), rect(3,7,1,2,"#FFD700"), px(5,7,"#FF0000"), px(6,7,"#4A90D9"), px(7,7,"#228B22")]

# --- SYMBOLS ---
def art_spiral(prompt, bg="#0a0a2e"):
    return "Spiral", [fill(bg), px(5,4,"#FF00FF"), px(6,4,"#FF00FF"), px(7,5,"#CC00CC"), px(7,6,"#CC00CC"), px(6,7,"#AA00AA"), px(5,7,"#AA00AA"), px(4,6,"#8800AA"), px(4,5,"#8800AA"), px(3,5,"#6600CC"), px(3,4,"#6600CC"), px(3,3,"#4400FF"), px(4,3,"#4400FF"), px(5,3,"#4400FF"), px(6,3,"#4400FF"), px(7,3,"#CC00CC")]

def art_dna(prompt, bg="#0a0a2e"):
    return "DNA", [fill(bg), px(3,1,"#4A90D9"), px(6,1,"#228B22"), px(4,2,"#ADD8E6"), px(5,2,"#90EE90"), px(5,3,"#4A90D9"), px(4,3,"#228B22"), px(6,4,"#4A90D9"), px(3,4,"#228B22"), px(6,5,"#ADD8E6"), px(3,5,"#90EE90"), px(5,6,"#4A90D9"), px(4,6,"#228B22"), px(4,7,"#ADD8E6"), px(5,7,"#90EE90"), px(3,8,"#4A90D9"), px(6,8,"#228B22"), px(3,9,"#ADD8E6"), px(6,9,"#90EE90"), px(4,10,"#4A90D9"), px(5,10,"#228B22"), px(5,11,"#ADD8E6"), px(4,11,"#90EE90")]

def art_infinity(prompt, bg="#0a0a2e"):
    return "Infinity", [fill(bg), px(2,5,"#FFD700"), px(1,6,"#FFD700"), px(2,7,"#FFD700"), px(3,6,"#FFD700"), px(4,5,"#FFD700"), px(5,6,"#FFD700"), px(6,5,"#FFD700"), px(7,6,"#FFD700"), px(8,5,"#FFD700"), px(7,4,"#FFD700"), px(8,7,"#FFD700"), px(2,4,"#FFD700")]

def art_at_sign(prompt, bg="#0a0a2e"):
    return "At Sign", [fill(bg), rect(3,4,4,1,"#00FF88"), rect(2,5,1,4,"#00FF88"), rect(7,5,1,4,"#00FF88"), rect(3,9,5,1,"#00FF88"), rect(5,6,2,2,"#00FF88"), px(4,6,"#00FF88"), px(4,7,"#00FF88")]

def art_exclamation(prompt, bg="#0a0a2e"):
    return "Exclamation", [fill(bg), rect(4,2,2,7,"#FF4444"), rect(4,10,2,2,"#FF4444")]

def art_question_mark(prompt, bg="#0a0a2e"):
    return "Question Mark", [fill(bg), rect(3,2,4,1,"#FFD700"), px(7,3,"#FFD700"), px(7,4,"#FFD700"), px(6,5,"#FFD700"), px(5,6,"#FFD700"), px(5,7,"#FFD700"), rect(5,9,1,2,"#FFD700"), px(2,3,"#FFD700")]

def art_checkmark(prompt, bg="#0a0a2e"):
    return "Check", [fill(bg), px(2,7,"#00FF00"), px(3,8,"#00FF00"), px(4,9,"#00FF00"), px(5,8,"#00FF00"), px(6,7,"#00FF00"), px(7,6,"#00FF00"), px(8,5,"#00FF00")]

def art_x_mark(prompt, bg="#0a0a2e"):
    return "X Mark", [fill(bg), px(2,3,"#FF0000"), px(3,4,"#FF0000"), px(4,5,"#FF0000"), px(5,6,"#FF0000"), px(6,7,"#FF0000"), px(7,8,"#FF0000"), px(7,3,"#FF0000"), px(6,4,"#FF0000"), px(5,5,"#FF0000"), px(4,6,"#FF0000"), px(3,7,"#FF0000"), px(2,8,"#FF0000")]

def art_equals(prompt, bg="#0a0a2e"):
    return "Equals", [fill(bg), rect(2,5,6,1,"#FFFFFF"), rect(2,8,6,1,"#FFFFFF")]

def art_ampersand(prompt, bg="#0a0a2e"):
    return "Ampersand", [fill(bg), px(4,3,"#FFD700"), px(3,4,"#FFD700"), px(5,4,"#FFD700"), px(3,5,"#FFD700"), px(4,5,"#FFD700"), px(4,6,"#FFD700"), px(3,7,"#FFD700"), px(5,7,"#FFD700"), px(6,6,"#FFD700"), px(2,8,"#FFD700"), px(6,8,"#FFD700"), px(3,9,"#FFD700"), px(7,9,"#FFD700")]

def art_brackets(prompt, bg="#0a0a2e"):
    return "Brackets", [fill(bg), rect(2,3,1,8,"#00FF88"), px(3,3,"#00FF88"), px(3,10,"#00FF88"), rect(7,3,1,8,"#00FF88"), px(6,3,"#00FF88"), px(6,10,"#00FF88")]

# --- VEHICLES ---
def art_car(prompt, bg="#87CEEB"):
    return "Car", [fill(bg), rect(1,6,8,3,"#FF0000"), rect(3,4,4,2,"#ADD8E6"), px(2,9,"#333333"), px(7,9,"#333333"), rect(0,10,10,4,"#666666")]

def art_truck(prompt, bg="#87CEEB"):
    return "Truck", [fill(bg), rect(0,5,6,4,"#FF0000"), rect(6,3,3,6,"#CC0000"), rect(7,4,2,3,"#ADD8E6"), px(1,9,"#333333"), px(7,9,"#333333"), rect(0,10,10,4,"#666666")]

def art_bus(prompt, bg="#87CEEB"):
    return "Bus", [fill(bg), rect(1,4,8,5,"#FFD700"), rect(2,5,2,2,"#ADD8E6"), rect(5,5,2,2,"#ADD8E6"), px(2,9,"#333333"), px(7,9,"#333333"), rect(0,10,10,4,"#666666")]

def art_train(prompt, bg="#87CEEB"):
    return "Train", [fill(bg), rect(1,5,7,4,"#4A90D9"), rect(1,4,7,1,"#333333"), rect(2,6,2,2,"#ADD8E6"), rect(5,6,2,2,"#ADD8E6"), rect(8,5,1,4,"#FF0000"), px(2,9,"#333333"), px(6,9,"#333333"), rect(0,10,10,4,"#666666")]

def art_helicopter(prompt, bg="#87CEEB"):
    return "Helicopter", [fill(bg), rect(1,3,8,1,"#666666"), rect(3,4,4,3,"#4A90D9"), px(7,5,"#4A90D9"), px(8,5,"#FF0000"), px(3,7,"#333333"), rect(2,5,1,2,"#ADD8E6")]

def art_sailboat(prompt, bg="#006994"):
    return "Sailboat", [fill(bg), rect(1,9,8,2,"#8B4513"), px(5,3,"#FFFFFF"), px(5,4,"#FFFFFF"), px(4,4,"#FFFFFF"), px(5,5,"#FFFFFF"), px(4,5,"#FFFFFF"), px(3,5,"#FFFFFF"), px(5,6,"#FFFFFF"), px(4,6,"#FFFFFF"), px(3,6,"#FFFFFF"), px(5,7,"#FFFFFF"), px(4,7,"#FFFFFF"), rect(5,3,1,6,"#8B4513"), rect(0,11,10,3,"#004466")]

def art_submarine(prompt, bg="#006994"):
    return "Submarine", [fill(bg), rect(1,6,8,3,"#FFD700"), px(0,7,"#FFD700"), px(9,7,"#FFD700"), rect(4,4,2,2,"#CCCCCC"), px(3,7,"#000066"), px(6,7,"#000066")]

def art_spaceship(prompt, bg="#0a0a2e"):
    return "Spaceship", [fill(bg), px(1,1,"#FFF"), px(8,3,"#FFF"), px(3,0,"#FFF"), px(4,3,"#CCCCCC"), px(5,3,"#CCCCCC"), rect(3,4,4,4,"#CCCCCC"), px(4,5,"#4A90D9"), px(5,5,"#4A90D9"), px(2,7,"#CCCCCC"), px(7,7,"#CCCCCC"), px(4,8,"#FF4444"), px(5,8,"#FF6600"), px(4,9,"#FF6600"), px(5,9,"#FFD700")]

def art_ufo(prompt, bg="#0a0a2e"):
    return "UFO", [fill(bg), px(1,0,"#FFF"), px(8,2,"#FFF"), px(5,1,"#FFF"), rect(3,5,4,2,"#CCCCCC"), rect(1,7,8,1,"#888888"), px(0,7,"#00FF00"), px(9,7,"#00FF00"), rect(4,4,2,1,"#00FF00"), px(3,8,"#FFFF00"), px(5,9,"#FFFF00"), px(7,8,"#FFFF00")]

def art_hot_air_balloon(prompt, bg="#87CEEB"):
    return "Hot Air Balloon", [fill(bg), rect(3,2,4,5,"#FF4444"), px(2,3,"#FF6B4A"), px(7,3,"#FF6B4A"), px(2,4,"#FFD700"), px(7,4,"#FFD700"), px(2,5,"#228B22"), px(7,5,"#228B22"), px(4,7,"#D2691E"), px(5,7,"#D2691E"), rect(4,8,2,2,"#8B4513")]

# --- SPORTS ---
def art_basketball(prompt, bg="#0a0a2e"):
    return "Basketball", [fill(bg), rect(3,4,4,4,"#FF8C00"), px(2,5,"#FF8C00"), px(7,5,"#FF8C00"), px(2,6,"#FF8C00"), px(7,6,"#FF8C00"), px(3,3,"#FF6B00"), px(6,3,"#FF6B00"), line(5,3,5,8,"#8B4513"), line(2,6,7,6,"#8B4513")]

def art_soccer(prompt, bg="#228B22"):
    return "Soccer Ball", [fill(bg), rect(3,4,4,4,"#FFFFFF"), px(2,5,"#FFFFFF"), px(7,5,"#FFFFFF"), px(2,6,"#FFFFFF"), px(7,6,"#FFFFFF"), px(4,5,"#000000"), px(5,5,"#000000"), px(4,6,"#000000"), px(5,6,"#000000")]

def art_football(prompt, bg="#228B22"):
    return "Football", [fill(bg), rect(3,5,4,3,"#8B4513"), px(2,6,"#8B4513"), px(7,6,"#8B4513"), line(5,5,5,7,"#FFFFFF"), px(4,6,"#FFFFFF"), px(6,6,"#FFFFFF")]

def art_tennis(prompt, bg="#0a0a2e"):
    return "Tennis", [fill(bg), rect(3,3,4,4,"#00FF00"), px(2,4,"#00FF00"), px(7,4,"#00FF00"), px(2,5,"#00FF00"), px(7,5,"#00FF00"), line(2,4,7,4,"#FFFFFF"), px(5,7,"#8B4513"), px(5,8,"#8B4513"), px(5,9,"#8B4513"), rect(4,10,3,1,"#8B4513")]

def art_baseball(prompt, bg="#228B22"):
    return "Baseball Bat", [fill(bg), line(2,9,7,4,"#D2691E"), px(7,3,"#D2691E"), px(8,3,"#D2691E"), rect(3,6,3,3,"#FFFFFF"), px(4,6,"#FF0000"), px(4,8,"#FF0000")]

def art_skateboard(prompt, bg="#87CEEB"):
    return "Skateboard", [fill(bg), rect(1,7,8,1,"#FF4444"), px(0,7,"#FF4444"), px(9,7,"#FF4444"), px(2,8,"#333333"), px(7,8,"#333333")]

def art_surfboard(prompt, bg="#006994"):
    return "Surfboard", [fill(bg), px(4,2,"#FFD700"), px(5,2,"#FFD700"), rect(4,3,2,8,"#FFD700"), px(4,11,"#FFD700"), px(5,11,"#FFD700"), line(4,4,4,10,"#FF6B4A")]

def art_dumbbell(prompt, bg="#0a0a2e"):
    return "Dumbbell", [fill(bg), rect(1,5,2,4,"#888888"), rect(7,5,2,4,"#888888"), rect(3,6,4,2,"#CCCCCC")]

def art_medal(prompt, bg="#0a0a2e"):
    return "Medal", [fill(bg), px(3,2,"#FFD700"), px(6,2,"#FFD700"), line(3,2,4,4,"#4A90D9"), line(6,2,5,4,"#FF0000"), rect(3,5,4,4,"#FFD700"), px(2,6,"#FFD700"), px(7,6,"#FFD700"), px(5,6,"#FFAA00"), px(4,7,"#FFAA00")]

# --- BUILDINGS ---
def art_cottage(prompt, bg="#87CEEB"):
    return "Cottage", [fill(bg), rect(2,7,6,5,"#D2691E"), px(4,5,"#8B0000"), px(5,5,"#8B0000"), rect(3,6,4,1,"#8B0000"), rect(2,7,6,1,"#8B0000"), rect(4,9,2,3,"#8B4513"), px(3,8,"#FFD700"), px(6,8,"#FFD700"), rect(0,12,10,2,"#228B22")]

def art_mansion(prompt, bg="#87CEEB"):
    return "Mansion", [fill(bg), rect(1,6,8,6,"#F5DEB3"), rect(2,4,6,2,"#F5DEB3"), rect(4,2,2,2,"#F5DEB3"), px(4,1,"#666666"), rect(4,8,2,4,"#8B4513"), px(2,7,"#FFD700"), px(7,7,"#FFD700"), px(2,9,"#FFD700"), px(7,9,"#FFD700"), rect(0,12,10,2,"#228B22")]

def art_castle(prompt, bg="#87CEEB"):
    return "Castle", [fill(bg), rect(2,6,6,6,"#999999"), px(2,5,"#999999"), px(4,5,"#999999"), px(5,5,"#999999"), px(7,5,"#999999"), px(0,4,"#999999"), px(0,5,"#999999"), rect(0,6,2,6,"#999999"), px(9,4,"#999999"), px(9,5,"#999999"), rect(8,6,2,6,"#999999"), rect(4,9,2,3,"#8B4513")]

def art_lighthouse(prompt, bg="#0a0a2e"):
    return "Lighthouse", [fill(bg), rect(4,3,2,9,"#FFFFFF"), rect(3,3,4,1,"#FF0000"), rect(3,5,4,1,"#FF0000"), rect(3,7,4,1,"#FF0000"), px(4,2,"#FFD700"), px(5,2,"#FFD700"), rect(0,12,10,2,"#006994")]

def art_windmill(prompt, bg="#87CEEB"):
    return "Windmill", [fill(bg), rect(4,5,2,7,"#D2691E"), px(4,4,"#D2691E"), px(5,4,"#D2691E"), px(5,3,"#FFFFFF"), px(6,2,"#FFFFFF"), px(3,3,"#FFFFFF"), px(2,2,"#FFFFFF"), px(5,5,"#FFFFFF"), px(6,6,"#FFFFFF"), px(3,5,"#FFFFFF"), px(2,6,"#FFFFFF"), rect(0,12,10,2,"#228B22")]

def art_church(prompt, bg="#87CEEB"):
    return "Church", [fill(bg), rect(2,6,6,6,"#F5DEB3"), rect(4,3,2,3,"#F5DEB3"), px(4,2,"#FFD700"), px(5,2,"#FFD700"), px(4,1,"#FFD700"), rect(4,9,2,3,"#8B4513"), rect(0,12,10,2,"#228B22")]

def art_skyscraper(prompt, bg="#0a0a2e"):
    return "Skyscraper", [fill(bg), rect(3,1,4,12,"#4A90D9"), px(4,2,"#FFD700"), px(5,2,"#FFD700"), px(4,4,"#FFD700"), px(5,4,"#FFD700"), px(4,6,"#FFD700"), px(5,6,"#FFD700"), px(4,8,"#FFD700"), px(5,8,"#FFD700"), px(4,10,"#FFD700"), px(5,10,"#FFD700"), rect(0,13,10,1,"#333333")]

def art_pyramid(prompt, bg="#FFD700"):
    bg2 = "#87CEEB"
    return "Pyramid", [fill(bg2), px(5,4,"#D4A017"), px(4,5,"#D4A017"), px(6,5,"#D4A017"), rect(3,6,5,1,"#D4A017"), rect(2,7,7,1,"#C49000"), rect(1,8,9,1,"#C49000"), rect(0,9,10,1,"#B48000"), rect(0,10,10,4,"#C2B280")]

def art_bridge(prompt, bg="#87CEEB"):
    return "Bridge", [fill(bg), rect(0,8,10,1,"#FF0000"), px(2,4,"#FF0000"), px(2,5,"#FF0000"), px(2,6,"#FF0000"), px(2,7,"#FF0000"), px(7,4,"#FF0000"), px(7,5,"#FF0000"), px(7,6,"#FF0000"), px(7,7,"#FF0000"), line(2,4,4,7,"#FF0000"), line(7,4,5,7,"#FF0000"), rect(0,9,10,5,"#006994")]

def art_tent(prompt, bg="#0a0a2e"):
    return "Tent", [fill(bg), px(1,1,"#FFFFFF"), px(8,0,"#FFFFFF"), px(5,4,"#228B22"), rect(4,5,3,1,"#228B22"), rect(3,6,5,1,"#228B22"), rect(2,7,7,1,"#228B22"), rect(1,8,9,1,"#228B22"), rect(0,9,10,1,"#228B22"), px(4,7,"#8B4513"), px(5,7,"#8B4513"), px(4,8,"#8B4513"), px(5,8,"#8B4513"), rect(0,10,10,4,"#228B22")]

# --- FACES ---
def art_grin(prompt, bg="#FFD700"):
    return "Grin", [fill(bg), px(3,4,"#000000"), px(6,4,"#000000"), px(2,7,"#000000"), px(3,8,"#000000"), px(4,8,"#000000"), px(5,8,"#000000"), px(6,8,"#000000"), px(7,7,"#000000")]

def art_angry_face(prompt, bg="#FF4444"):
    return "Angry", [fill(bg), px(3,4,"#000000"), px(6,4,"#000000"), px(2,3,"#000000"), px(7,3,"#000000"), px(3,7,"#000000"), px(4,7,"#000000"), px(5,7,"#000000"), px(6,7,"#000000")]

def art_cry_face(prompt, bg="#4A90D9"):
    return "Crying", [fill(bg), px(3,4,"#000000"), px(6,4,"#000000"), px(3,5,"#00BFFF"), px(6,5,"#00BFFF"), px(3,6,"#00BFFF"), px(6,6,"#00BFFF"), px(3,8,"#000000"), px(4,9,"#000000"), px(5,9,"#000000"), px(6,8,"#000000")]

def art_sunglasses_face(prompt, bg="#FFD700"):
    return "Cool Face", [fill(bg), rect(2,4,3,2,"#000000"), rect(6,4,3,2,"#000000"), px(5,4,"#000000"), px(3,8,"#000000"), px(4,8,"#000000"), px(5,8,"#000000"), px(6,8,"#000000"), px(2,9,"#000000"), px(7,9,"#000000")]

def art_laugh_face(prompt, bg="#FFD700"):
    return "LOL", [fill(bg), px(3,3,"#000000"), px(6,3,"#000000"), px(2,4,"#000000"), px(4,4,"#000000"), px(5,4,"#000000"), px(7,4,"#000000"), px(2,7,"#000000"), px(3,8,"#000000"), px(4,8,"#000000"), px(5,8,"#000000"), px(6,8,"#000000"), px(7,7,"#000000")]

def art_sleepy_face(prompt, bg="#483D8B"):
    return "Sleepy", [fill(bg), line(2,4,4,4,"#FFD700"), line(5,4,7,4,"#FFD700"), px(3,7,"#FFD700"), px(4,8,"#FFD700"), px(5,8,"#FFD700"), px(6,7,"#FFD700"), text("Z",7,1,"#FFFFFF")]

def art_heart_eyes(prompt, bg="#FFD700"):
    return "Heart Eyes", [fill(bg), px(2,3,"#FF0000"), px(4,3,"#FF0000"), px(3,4,"#FF0000"), px(5,3,"#FF0000"), px(7,3,"#FF0000"), px(6,4,"#FF0000"), px(3,8,"#000000"), px(4,8,"#000000"), px(5,8,"#000000"), px(6,8,"#000000"), px(2,9,"#000000"), px(7,9,"#000000")]

# --- HOLIDAY ---
def art_skull(prompt, bg="#0a0a2e"):
    return "Skull", [fill(bg), rect(3,3,4,4,"#FFFFFF"), px(2,4,"#FFFFFF"), px(7,4,"#FFFFFF"), px(4,4,"#000000"), px(5,4,"#000000"), px(4,6,"#000000"), px(3,7,"#000000"), px(4,7,"#000000"), px(5,7,"#000000"), px(6,7,"#000000"), rect(3,8,4,1,"#FFFFFF"), px(3,8,"#000000"), px(5,8,"#000000")]

def art_jack_o_lantern(prompt, bg="#0a0a2e"):
    return "Jack O Lantern", [fill(bg), rect(2,4,6,6,"#FF8C00"), px(1,5,"#FF8C00"), px(8,5,"#FF8C00"), px(4,3,"#228B22"), px(5,3,"#228B22"), px(5,2,"#228B22"), px(3,5,"#FFD700"), px(6,5,"#FFD700"), rect(3,8,4,1,"#FFD700"), px(4,7,"#FFD700"), px(5,7,"#FFD700")]

def art_witch_hat(prompt, bg="#0a0a2e"):
    return "Witch Hat", [fill(bg), px(5,2,"#333333"), rect(4,3,2,2,"#333333"), rect(3,5,4,2,"#333333"), rect(2,7,6,2,"#333333"), rect(1,9,8,1,"#333333"), px(4,5,"#FFD700"), px(5,5,"#FFD700")]

def art_santa_hat(prompt, bg="#0a0a2e"):
    return "Santa Hat", [fill(bg), px(5,2,"#FFFFFF"), rect(4,3,3,1,"#FF0000"), rect(3,4,4,2,"#FF0000"), rect(2,6,6,2,"#FF0000"), rect(1,8,8,1,"#FFFFFF")]

def art_menorah(prompt, bg="#0a0a2e"):
    return "Menorah", [fill(bg), rect(4,4,2,7,"#FFD700"), px(1,5,"#FFD700"), px(2,5,"#FFD700"), px(3,5,"#FFD700"), px(6,5,"#FFD700"), px(7,5,"#FFD700"), px(8,5,"#FFD700"), rect(1,6,1,5,"#FFD700"), rect(8,6,1,5,"#FFD700"), px(1,4,"#FFAA00"), px(4,3,"#FFAA00"), px(5,3,"#FFAA00"), px(8,4,"#FFAA00")]

def art_dreidel(prompt, bg="#0a0a2e"):
    return "Dreidel", [fill(bg), px(4,3,"#4A90D9"), px(5,3,"#4A90D9"), rect(3,4,4,5,"#4A90D9"), px(4,9,"#4A90D9"), px(5,9,"#4A90D9"), px(5,10,"#4A90D9"), px(4,5,"#FFD700"), px(5,6,"#FFD700"), px(4,7,"#FFD700")]

def art_easter_egg(prompt, bg="#228B22"):
    return "Easter Egg", [fill(bg), px(4,3,"#FF69B4"), px(5,3,"#FF69B4"), rect(3,4,4,5,"#FF69B4"), px(2,5,"#FF69B4"), px(7,5,"#FF69B4"), px(4,9,"#FF69B4"), px(5,9,"#FF69B4"), rect(3,5,4,1,"#FFD700"), rect(3,7,4,1,"#4A90D9")]

def art_firework(prompt, bg="#0a0a2e"):
    return "Firework", [fill(bg), px(5,4,"#FFD700"), px(4,3,"#FF0000"), px(6,3,"#FF0000"), px(3,4,"#FF4444"), px(7,4,"#FF4444"), px(4,5,"#FFAA00"), px(6,5,"#FFAA00"), px(3,2,"#FF6666"), px(7,2,"#FF6666"), px(2,5,"#FF6666"), px(8,5,"#FF6666"), px(5,6,"#FFAA00"), px(5,2,"#FF6666")]

def art_present(prompt, bg="#0a0a2e"):
    return "Present", [fill(bg), rect(2,5,6,5,"#FF0000"), rect(4,5,2,5,"#FFD700"), rect(2,5,6,1,"#FFD700"), px(4,3,"#FFD700"), px(5,3,"#FFD700"), px(3,4,"#FFD700"), px(6,4,"#FFD700")]

def art_party_hat(prompt, bg="#0a0a2e"):
    return "Party Hat", [fill(bg), px(5,2,"#FFFFFF"), px(4,3,"#FFD700"), px(5,3,"#FF00FF"), rect(3,4,4,2,"#FF00FF"), rect(2,6,6,2,"#FFD700"), rect(1,8,8,2,"#FF00FF"), px(3,5,"#00FF00"), px(6,6,"#00FF00")]

def art_clover(prompt, bg="#0a0a2e"):
    return "Four Leaf Clover", [fill(bg), rect(4,3,2,2,"#228B22"), rect(3,2,2,2,"#228B22"), rect(5,2,2,2,"#228B22"), rect(3,4,2,2,"#228B22"), rect(5,4,2,2,"#228B22"), px(5,6,"#228B22"), px(5,7,"#006400"), px(5,8,"#006400")]

# --- MISC ---
def art_moon_stars(prompt, bg="#0a0a2e"):
    return "Moon And Stars", [fill(bg), rect(2,3,3,5,"#FFD700"), px(2,3,"#0a0a2e"), px(2,4,"#0a0a2e"), px(5,5,"#FFD700"), px(7,2,"#FFFFFF"), px(8,6,"#FFFFFF"), px(6,9,"#FFFFFF"), px(1,8,"#FFFFFF")]

def art_diamond_ring(prompt, bg="#0a0a2e"):
    return "Diamond Ring", [fill(bg), px(4,3,"#00BFFF"), px(5,3,"#00BFFF"), px(3,4,"#ADD8E6"), px(6,4,"#ADD8E6"), px(4,4,"#FFFFFF"), px(5,4,"#FFFFFF"), rect(3,5,4,1,"#FFD700"), rect(3,6,4,4,"#FFD700"), px(2,7,"#FFD700"), px(7,7,"#FFD700")]

def art_trident(prompt, bg="#006994"):
    return "Trident", [fill(bg), rect(4,4,2,8,"#FFD700"), px(2,3,"#FFD700"), px(2,4,"#FFD700"), px(3,4,"#FFD700"), px(7,3,"#FFD700"), px(7,4,"#FFD700"), px(6,4,"#FFD700"), px(4,2,"#FFD700"), px(5,2,"#FFD700")]

def art_kite(prompt, bg="#87CEEB"):
    return "Kite", [fill(bg), px(5,2,"#FF4444"), px(4,3,"#FF4444"), px(6,3,"#FF4444"), px(5,3,"#FFD700"), rect(3,4,5,1,"#FF4444"), px(5,5,"#FF4444"), px(4,5,"#FFD700"), px(6,5,"#FFD700"), px(5,6,"#FF4444"), px(5,7,"#8B4513"), px(5,8,"#8B4513"), px(6,9,"#8B4513")]

def art_dice(prompt, bg="#228B22"):
    return "Dice", [fill(bg), rect(1,4,4,5,"#FFFFFF"), rect(6,4,3,5,"#FFFFFF"), px(2,5,"#000000"), px(4,5,"#000000"), px(3,7,"#000000"), px(2,8,"#000000"), px(4,8,"#000000"), px(7,5,"#000000"), px(7,7,"#000000")]

def art_crystal_ball(prompt, bg="#0a0a2e"):
    return "Crystal Ball", [fill(bg), rect(3,3,4,5,"#9370DB"), px(2,4,"#9370DB"), px(7,4,"#9370DB"), px(2,5,"#9370DB"), px(7,5,"#9370DB"), px(4,4,"#E6E6FA"), px(3,5,"#E6E6FA"), rect(3,8,4,1,"#FFD700"), rect(2,9,6,1,"#FFD700")]

def art_pirate_flag(prompt, bg="#000000"):
    return "Pirate Flag", [fill(bg), rect(3,3,4,3,"#FFFFFF"), px(4,3,"#000000"), px(5,3,"#000000"), px(4,4,"#FFFFFF"), px(5,4,"#FFFFFF"), px(4,5,"#000000"), px(2,6,"#FFFFFF"), px(7,6,"#FFFFFF"), px(3,7,"#FFFFFF"), px(6,7,"#FFFFFF"), rect(1,2,1,10,"#8B4513")]

def art_flip_flop(prompt, bg="#C2B280"):
    return "Flip Flop", [fill(bg), rect(3,4,4,6,"#FF6B4A"), px(2,5,"#FF6B4A"), px(7,5,"#FF6B4A"), px(4,4,"#8B4513"), px(5,4,"#8B4513"), px(3,5,"#8B4513"), px(6,5,"#8B4513")]

def art_viking_helmet(prompt, bg="#0a0a2e"):
    return "Viking Helmet", [fill(bg), rect(2,5,6,4,"#888888"), px(1,4,"#FFD700"), px(8,4,"#FFD700"), px(0,3,"#FFD700"), px(9,3,"#FFD700"), rect(3,4,4,1,"#AAAAAA"), px(4,6,"#000000"), px(5,6,"#000000")]

def art_totem_pole(prompt, bg="#0a0a2e"):
    return "Totem Pole", [fill(bg), rect(3,1,4,12,"#8B4513"), px(4,2,"#FF0000"), px(5,2,"#FF0000"), px(4,3,"#FFFFFF"), px(5,3,"#FFFFFF"), px(2,4,"#8B4513"), px(7,4,"#8B4513"), px(4,6,"#FFD700"), px(5,6,"#FFD700"), px(4,7,"#000000"), px(5,7,"#000000"), px(3,9,"#FF0000"), px(6,9,"#FF0000"), px(4,10,"#228B22"), px(5,10,"#228B22")]

def art_wings(prompt, bg="#87CEEB"):
    return "Wings", [fill(bg), px(4,5,"#FFFFFF"), px(5,5,"#FFFFFF"), px(3,4,"#FFFFFF"), px(6,4,"#FFFFFF"), px(2,3,"#FFFFFF"), px(7,3,"#FFFFFF"), px(1,2,"#FFFFFF"), px(8,2,"#FFFFFF"), px(0,2,"#FFFFFF"), px(9,2,"#FFFFFF"), px(3,5,"#E6E6FA"), px(6,5,"#E6E6FA"), px(2,4,"#E6E6FA"), px(7,4,"#E6E6FA")]

def art_halo(prompt, bg="#0a0a2e"):
    return "Halo", [fill(bg), px(3,3,"#FFD700"), px(4,2,"#FFD700"), px(5,2,"#FFD700"), px(6,3,"#FFD700"), px(3,4,"#FFD700"), px(6,4,"#FFD700")]

def art_eye(prompt, bg="#0a0a2e"):
    return "Eye", [fill(bg), rect(2,5,6,4,"#FFFFFF"), px(1,6,"#FFFFFF"), px(8,6,"#FFFFFF"), rect(4,6,2,2,"#4A90D9"), px(4,6,"#000000"), px(5,7,"#000000")]

def art_jellyfish(prompt, bg="#006994"):
    return "Jellyfish", [fill(bg), rect(3,3,4,3,"#FF69B4"), px(2,4,"#FF69B4"), px(7,4,"#FF69B4"), px(3,6,"#FFB6C1"), px(4,7,"#FFB6C1"), px(5,6,"#FFB6C1"), px(6,7,"#FFB6C1"), px(3,8,"#FFB6C1"), px(5,8,"#FFB6C1"), px(4,9,"#FFB6C1"), px(6,9,"#FFB6C1")]

def art_dinosaur(prompt, bg="#0a0a2e"):
    return "Dinosaur", [fill(bg), rect(5,3,3,3,"#228B22"), px(7,3,"#000000"), rect(3,5,4,4,"#228B22"), px(2,6,"#228B22"), px(2,7,"#228B22"), px(3,9,"#228B22"), px(5,9,"#228B22"), px(7,6,"#228B22"), px(8,5,"#228B22")]

def art_peacock(prompt, bg="#0a0a2e"):
    return "Peacock", [fill(bg), rect(4,7,2,4,"#008B8B"), px(4,6,"#008B8B"), px(5,6,"#008B8B"), px(5,5,"#008B8B"), px(2,3,"#00BFFF"), px(3,2,"#00FF00"), px(5,2,"#FFD700"), px(7,3,"#00FF00"), px(1,4,"#00BFFF"), px(8,4,"#00BFFF"), px(3,3,"#4A90D9"), px(6,3,"#4A90D9")]

def art_scorpion(prompt, bg="#C2B280"):
    return "Scorpion", [fill(bg), rect(3,6,4,2,"#8B0000"), px(2,7,"#8B0000"), px(7,7,"#8B0000"), px(1,6,"#8B0000"), px(8,6,"#8B0000"), px(1,5,"#8B0000"), px(5,5,"#8B0000"), px(6,4,"#8B0000"), px(7,3,"#8B0000"), px(7,2,"#FF0000")]

def art_dragonfly(prompt, bg="#87CEEB"):
    return "Dragonfly", [fill(bg), rect(4,5,2,5,"#00BFFF"), px(1,4,"#ADD8E6"), px(2,5,"#ADD8E6"), px(3,4,"#ADD8E6"), px(6,4,"#ADD8E6"), px(7,5,"#ADD8E6"), px(8,4,"#ADD8E6"), px(4,4,"#00BFFF"), px(5,4,"#00BFFF"), px(4,3,"#FF0000"), px(5,3,"#FF0000")]

def art_lobster(prompt, bg="#006994"):
    return "Lobster", [fill(bg), rect(4,5,2,4,"#FF0000"), px(3,5,"#FF0000"), px(6,5,"#FF0000"), px(2,4,"#FF0000"), px(7,4,"#FF0000"), px(1,3,"#CC0000"), px(8,3,"#CC0000"), px(1,4,"#CC0000"), px(8,4,"#CC0000"), px(4,4,"#000000"), px(5,4,"#000000")]

def art_cabin(prompt, bg="#0a0a2e"):
    return "Log Cabin", [fill(bg), rect(2,6,6,6,"#8B4513"), px(4,4,"#6B3410"), px(5,4,"#6B3410"), rect(3,5,4,1,"#6B3410"), rect(4,8,2,4,"#4A2F1A"), px(3,7,"#FFD700"), px(6,7,"#FFD700"), px(1,1,"#FFFFFF"), px(8,0,"#FFFFFF"), rect(0,12,10,2,"#228B22")]

def art_roller_coaster(prompt, bg="#87CEEB"):
    return "Roller Coaster", [fill(bg), px(1,8,"#FF0000"), px(2,6,"#FF0000"), px(3,4,"#FF0000"), px(4,3,"#FF0000"), px(5,3,"#FF0000"), px(6,5,"#FF0000"), px(7,7,"#FF0000"), px(8,8,"#FF0000"), px(4,2,"#4A90D9"), px(5,2,"#4A90D9"), line(1,9,1,12,"#888888"), line(4,4,4,12,"#888888"), line(8,9,8,12,"#888888")]

def art_magnifying_glass(prompt, bg="#0a0a2e"):
    return "Magnifying Glass", [fill(bg), rect(3,3,3,3,"#ADD8E6"), px(2,4,"#FFD700"), px(6,4,"#FFD700"), px(3,2,"#FFD700"), px(5,2,"#FFD700"), px(2,5,"#FFD700"), px(6,5,"#FFD700"), px(3,6,"#FFD700"), px(5,6,"#FFD700"), px(6,7,"#8B4513"), px(7,8,"#8B4513"), px(8,9,"#8B4513")]

def art_stop_sign(prompt, bg="#87CEEB"):
    return "Stop Sign", [fill(bg), rect(2,4,6,6,"#FF0000"), px(2,3,"#FF0000"), px(7,3,"#FF0000"), px(2,10,"#FF0000"), px(7,10,"#FF0000"), text("STOP",1,6,"#FFFFFF"), rect(4,10,2,3,"#888888")]


# ============================================================
# SUBJECT CLASSIFICATION
# ============================================================

SUBJECT_MAP = {}

def register(keywords, art_fn):
    for kw in keywords:
        SUBJECT_MAP[kw] = art_fn

# Animals (lines 0-154 already done, but some might need filling)
# Trees/plants
register(['pine tree', 'pine', 'christmas tree looking'], art_pine_tree)
register(['oak tree', 'oak'], art_oak_tree)
register(['palm tree', 'palm', 'tropical'], art_palm_tree)
register(['willow', 'weeping willow'], art_willow)
register(['cherry blossom', 'cherry bloom'], art_cherry_blossom)
register(['lotus', 'lotus flower'], art_lotus)
register(['cactus'], art_cactus)
register(['mushroom'], art_mushroom)
register(['bamboo'], art_bamboo)
register(['acorn'], art_acorn)
register(['pinecone'], art_pinecone)
register(['coral', 'reef'], art_coral)
register(['seashell', 'shell'], art_seashell)
# Landscape
register(['waterfall'], art_waterfall)
register(['mountain', 'mountains'], art_mountain)
register(['volcano', 'erupting'], art_volcano)
register(['sun with', 'sun ray', 'bright sun', 'yellow sun', 'orange sun', 'cheerful sun', 'warm sun'], art_sun)
register(['sunset scene', 'sunset over', 'beautiful sunset', 'pink sunset', 'purple and gold'], art_sunset_scene)
register(['cloud', 'rain cloud', 'rain'], art_cloud_rain)
register(['rainbow arc', 'rainbow', 'colorful rainbow'], art_rainbow)
register(['wave', 'ocean wave', 'great wave'], art_wave)
# Food
register(['apple'], art_apple)
register(['banana'], art_banana)
register(['pizza'], art_pizza)
register(['ice cream'], art_ice_cream)
register(['cupcake'], art_cupcake)
register(['coffee', 'mug'], art_coffee)
register(['wine glass', 'wine'], art_wine_glass)
register(['burger', 'hamburger', 'cheeseburger'], art_burger)
register(['donut', 'doughnut'], art_donut)
register(['watermelon'], art_watermelon)
register(['cherr'], art_cherry)
register(['grape'], art_grapes)
register(['carrot'], art_carrot)
register(['corn'], art_corn)
register(['cookie'], art_cookie)
register(['lollipop'], art_lollipop)
register(['popsicle'], art_popsicle)
register(['sushi'], art_sushi)
register(['taco'], art_taco)
register(['pretzel'], art_pretzel)
# Tech
register(['smartphone', 'phone'], art_smartphone)
register(['laptop', 'computer'], art_laptop)
register(['game controller', 'gamepad', 'game pad', 'controller', 'playstation'], art_gamepad)
register(['headphone'], art_headphones)
register(['camera'], art_camera)
register(['battery'], art_battery)
register(['power button', 'power'], art_power_button)
register(['play', 'pause'], art_play_pause)
register(['mic', 'microphone'], art_microphone)
register(['satellite'], art_satellite)
register(['drone'], art_drone)
register(['robot'], art_robot)
register(['arcade'], art_arcade)
register(['spiral'], art_spiral)
register(['dna', 'helix'], art_dna)
register(['infinity'], art_infinity)
register(['at sign', '@ sign'], art_at_sign)
register(['exclamation'], art_exclamation)
register(['question mark'], art_question_mark)
register(['check mark', 'checkmark'], art_checkmark)
register(['red x', 'big x'], art_x_mark)
register(['equal', 'equals'], art_equals)
register(['ampersand', 'and sign'], art_ampersand)
register(['bracket'], art_brackets)
# Vehicles
register(['car'], art_car)
register(['truck'], art_truck)
register(['bus'], art_bus)
register(['train'], art_train)
register(['helicopter'], art_helicopter)
register(['sailboat', 'sail boat'], art_sailboat)
register(['submarine'], art_submarine)
register(['spaceship', 'space ship'], art_spaceship)
register(['ufo', 'flying saucer'], art_ufo)
register(['hot air balloon', 'balloon'], art_hot_air_balloon)
# Sports
register(['basketball'], art_basketball)
register(['soccer', 'soccer ball'], art_soccer)
register(['football'], art_football)
register(['tennis'], art_tennis)
register(['baseball', 'bat'], art_baseball)
register(['skateboard'], art_skateboard)
register(['surfboard'], art_surfboard)
register(['dumbbell', 'weight'], art_dumbbell)
register(['medal'], art_medal)
# Buildings
register(['cottage'], art_cottage)
register(['mansion'], art_mansion)
register(['castle'], art_castle)
register(['lighthouse'], art_lighthouse)
register(['windmill'], art_windmill)
register(['church'], art_church)
register(['skyscraper'], art_skyscraper)
register(['pyramid'], art_pyramid)
register(['bridge', 'golden gate'], art_bridge)
register(['tent', 'camping'], art_tent)
# Faces
register(['grin', 'smiley', 'happy face', 'smile'], art_grin)
register(['angry face', 'grumpy'], art_angry_face)
register(['crying', 'cry face', 'sad face'], art_cry_face)
register(['sunglasses', 'cool face'], art_sunglasses_face)
register(['laughing', 'lol'], art_laugh_face)
register(['sleepy face', 'tired face', 'zzz'], art_sleepy_face)
register(['heart eyes'], art_heart_eyes)
# Holiday
register(['skull', 'crossbone'], art_skull)
register(['jack-o-lantern', 'jack o lantern', 'halloween pumpkin', 'carved pumpkin'], art_jack_o_lantern)
register(['witch hat', "witch's hat"], art_witch_hat)
register(['santa hat', 'santa'], art_santa_hat)
register(['menorah'], art_menorah)
register(['dreidel'], art_dreidel)
register(['easter egg'], art_easter_egg)
register(['firework'], art_firework)
register(['present', 'gift', 'wrapped'], art_present)
register(['party hat'], art_party_hat)
register(['clover', 'four leaf', 'shamrock'], art_clover)
# Misc
register(['moon', 'star'], art_moon_stars)
register(['diamond ring', 'ring'], art_diamond_ring)
register(['trident'], art_trident)
register(['kite'], art_kite)
register(['dice'], art_dice)
register(['crystal ball'], art_crystal_ball)
register(['pirate flag', 'pirate', 'jolly roger'], art_pirate_flag)
register(['flip flop', 'sandal'], art_flip_flop)
register(['viking', 'helmet'], art_viking_helmet)
register(['totem pole', 'totem'], art_totem_pole)
register(['wing'], art_wings)
register(['halo'], art_halo)
register(['eye'], art_eye)
register(['jellyfish'], art_jellyfish)
register(['dinosaur', 'dino', 't-rex', 'trex'], art_dinosaur)
register(['peacock'], art_peacock)
register(['scorpion'], art_scorpion)
register(['dragonfly'], art_dragonfly)
register(['lobster'], art_lobster)
register(['cabin', 'log cabin'], art_cabin)
register(['roller coaster'], art_roller_coaster)
register(['magnifying glass'], art_magnifying_glass)
register(['stop sign'], art_stop_sign)


def find_art_function(prompt):
    """Find the best matching art function for a prompt."""
    p = prompt.lower()
    # Try exact subject matches (longer keywords first for specificity)
    sorted_keywords = sorted(SUBJECT_MAP.keys(), key=lambda k: -len(k))
    for kw in sorted_keywords:
        if kw in p:
            return SUBJECT_MAP[kw]
    return None


def generate_render_response(prompt):
    """Generate a render response for a render_diverse prompt."""
    art_fn = find_art_function(prompt)
    if art_fn:
        name, elements = art_fn(prompt)
        # Vary the name slightly based on prompt
        h = prompt_hash(prompt)
        return make_render_program(name, elements)

    # Fallback: generic pixel art (simple colored shape)
    h = prompt_hash(prompt)
    colors = ["#FF4444", "#FFD700", "#4A90D9", "#228B22", "#FF69B4", "#FF8C00", "#9370DB", "#00BFFF"]
    color = colors[h % len(colors)]
    bgs = ["#0a0a2e", "#1a1a3a", "#000000"]
    bg = bgs[h % len(bgs)]
    return make_render_program("Pixel Art", [
        fill(bg),
        rect(3, 4, 4, 4, color),
        px(2, 5, color),
        px(7, 5, color),
        px(4, 3, color),
        px(5, 3, color),
    ])


def generate_mixed_response(prompt):
    """Generate response for mixed category (render + pattern combination)."""
    p = prompt.lower()
    h = prompt_hash(prompt)

    # Try to find render art + add pattern
    art_fn = find_art_function(prompt)

    if art_fn:
        name, elements = art_fn(prompt)
        # Add ambient/pattern step
        pattern_steps = [
            {"id": "show", "command": {"type": "render", "elements": elements}, "duration": None}
        ]

        if 'ambient' in p or 'glow' in p or 'twinkl' in p:
            ambient_colors = ["#FF6B4A", "#4A90D9", "#228B22", "#9370DB", "#FFD700", "#FF69B4"]
            ac = ambient_colors[h % len(ambient_colors)]
            if 'twinkl' in p or 'sparkl' in p:
                pattern_steps.append({"id": "ambient", "command": {"type": "pattern", "name": "sparkle", "params": {"color": ac, "bgColor": "#0a0a2e", "speed": 150, "density": 0.05}}, "duration": 5000})
            elif 'rainbow' in p:
                pattern_steps.append({"id": "ambient", "command": {"type": "pattern", "name": "rainbow", "params": {"speed": 3000}}, "duration": 5000})
            else:
                pattern_steps.append({"id": "ambient", "command": {"type": "pattern", "name": "breathing", "params": {"color": ac, "speed": 3500}}, "duration": 5000})

            return make_multi_step_render(name, pattern_steps, {"count": 0, "start_step": "show", "end_step": "ambient"})

        return make_render_program(name, elements)

    # Fallback for mixed
    return make_render_program("Display", [
        fill("#0a0a2e"),
        rect(3, 4, 4, 4, "#FFD700"),
        px(2, 5, "#FFD700"),
        px(7, 5, "#FFD700"),
    ])


# ============================================================
# MAIN
# ============================================================

def main():
    input_path = "/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/finetuning/data/remaining_chunk_1.jsonl"
    output_path = "/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/finetuning/data/responses_chunk_1.jsonl"

    with open(input_path) as f:
        all_prompts = [json.loads(line.strip()) for line in f]

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

    new_responses = []
    unmatched = []
    for i, item in enumerate(remaining):
        prompt = item["prompt"]
        category = item.get("category", "render_diverse")

        if category == "mixed":
            response = generate_mixed_response(prompt)
        else:
            response = generate_render_response(prompt)

        # Validate
        try:
            parsed = json.loads(response)
            assert "program" in parsed
            assert "steps" in parsed["program"]
        except Exception as e:
            print(f"  ERROR at {i}: {prompt[:50]} -> {e}")
            # Use fallback
            response = make_render_program("Display", [fill("#0a0a2e"), rect(3,4,4,4,"#FFD700")])

        new_responses.append({"prompt": prompt, "response": response})

        # Track unmatched
        if find_art_function(prompt) is None and category != "mixed":
            unmatched.append(prompt[:60])

        if (i + 1) % 100 == 0:
            print(f"  Generated {i+1}/{len(remaining)}")

    # Write
    with open(output_path, 'w') as f:
        for resp in existing:
            f.write(json.dumps(resp) + "\n")
        for resp in new_responses:
            f.write(json.dumps(resp) + "\n")

    total = already_done + len(new_responses)
    print(f"\nDone! Total: {total}/{len(all_prompts)}")
    if unmatched:
        print(f"\nUnmatched prompts ({len(unmatched)}):")
        for p in unmatched[:20]:
            print(f"  - {p}")


if __name__ == "__main__":
    main()

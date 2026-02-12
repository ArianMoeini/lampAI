"""
Test: Do shape primitives improve pixel art output?

Compares two system prompts:
  A) Original — only pixel, rect, line, fill, text (model must invent coordinates)
  B) Enhanced — adds circle, triangle, star, diamond, heart primitives

Runs the 10 pixel art prompts through base gemma3:4b with both prompts,
then optionally through lamp-gemma-v2 (fine-tuned) with the enhanced prompt.

Usage:
  python3 test_primitives.py                    # base gemma3:4b only
  python3 test_primitives.py --also-finetuned   # + lamp-gemma-v2
  python3 test_primitives.py --send              # also send to lamp server
  python3 test_primitives.py --index 1           # run just one prompt
"""

import json
import time
import re
import argparse
import urllib.request

OLLAMA_URL = "http://localhost:11434"
LAMP_SERVER_URL = "http://localhost:3001"

# ── System prompt A: Original (no shape primitives) ──────────────────────
PROMPT_ORIGINAL = """You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

## Commands (use inside step.command):
- solid(color) — all LEDs one color
  {"type":"pattern","name":"solid","params":{"color":"#FF4444"}}
- gradient(color, color2) — radial blend, center to edge
  {"type":"pattern","name":"gradient","params":{"color":"#FF6B4A","color2":"#FFE4C4"}}
- breathing(color, speed) — pulsing glow. speed in ms (2000=calm, 500=urgent)
  {"type":"pattern","name":"breathing","params":{"color":"#4A90D9","speed":3000}}
- wave(color, color2, speed) — color ripple across rows
  {"type":"pattern","name":"wave","params":{"color":"#FF6B4A","color2":"#FFE4C4","speed":2000}}
- rainbow(speed) — cycling rainbow
  {"type":"pattern","name":"rainbow","params":{"speed":3000}}
- pulse(color, speed) — quick flash then fade, one-shot
  {"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":500}}
- sparkle(color, bgColor, speed, density) — random twinkling
  {"type":"pattern","name":"sparkle","params":{"color":"#FFF","bgColor":"#1a1a1a","speed":100,"density":0.1}}
- render(elements) — draw on the 10×14 grid using drawing tools
  {"type":"render","elements":[{"type":"fill","color":"#000"},{"type":"text","content":"HI","x":2,"y":4,"color":"#FFF"},{"type":"pixel","x":5,"y":1,"color":"#F44"},{"type":"rect","x":0,"y":12,"w":10,"h":2,"color":"#333"}]}
  Drawing tools: fill(color), text(content,x,y,color), pixel(x,y,color), rect(x,y,w,h,color), line(x1,y1,x2,y2,color)
  Grid: 10 wide × 14 tall. x=0 left, y=0 top. Text font: 3px wide per char + 1px gap. Use pixel for custom shapes.
  Combine render with patterns in multi-step programs.

## Program structure:
{"program":{"name":"...","steps":[{"id":"...","command":{...},"duration":ms_or_null}],"loop":{"count":N,"start_step":"id","end_step":"id"},"on_complete":{"command":{...}}}}
- duration: null = stays forever. milliseconds = auto-advance after that time.
- loop: optional. count=0 means infinite. Repeats from start_step to end_step.
- on_complete: optional. Runs when program finishes all steps/loops.

## Timing: 1min=60000, 5min=300000, 25min=1500000, 1hr=3600000. loop.count 0=infinite.

## Color moods:
Warm/cozy: #FF6B4A #FFE4C4 #D88B70 #FFBF00. Calm: #4A90D9 #008B8B #E6E6FA. Focus: #F0F8FF #ADD8E6. Sleep: #191970 #483D8B. Energy: #FF4444 #FF00FF #FFD700. Nature: #228B22 #8B4513. Romantic: #FFB6C1 #9370DB.

## Examples:

User: "warm and cozy"
{"program":{"name":"Warm Cozy","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#D88B70","color2":"#FFF0DC"}},"duration":null}]}}

User: "show a heart"
{"program":{"name":"Heart","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#1a0a1a"},{"type":"pixel","x":3,"y":4,"color":"#FF2266"},{"type":"pixel","x":6,"y":4,"color":"#FF2266"},{"type":"rect","x":2,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":5,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":3,"y":7,"w":4,"h":2,"color":"#FF2266"},{"type":"rect","x":4,"y":9,"w":2,"h":1,"color":"#FF2266"}]},"duration":null}]}}"""


# ── System prompt B: Enhanced (with shape primitives) ────────────────────
PROMPT_WITH_PRIMITIVES = """You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

## Commands (use inside step.command):
- solid(color) — all LEDs one color
  {"type":"pattern","name":"solid","params":{"color":"#FF4444"}}
- gradient(color, color2) — radial blend, center to edge
  {"type":"pattern","name":"gradient","params":{"color":"#FF6B4A","color2":"#FFE4C4"}}
- breathing(color, speed) — pulsing glow. speed in ms (2000=calm, 500=urgent)
  {"type":"pattern","name":"breathing","params":{"color":"#4A90D9","speed":3000}}
- wave(color, color2, speed) — color ripple across rows
  {"type":"pattern","name":"wave","params":{"color":"#FF6B4A","color2":"#FFE4C4","speed":2000}}
- rainbow(speed) — cycling rainbow
  {"type":"pattern","name":"rainbow","params":{"speed":3000}}
- pulse(color, speed) — quick flash then fade, one-shot
  {"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":500}}
- sparkle(color, bgColor, speed, density) — random twinkling
  {"type":"pattern","name":"sparkle","params":{"color":"#FFF","bgColor":"#1a1a1a","speed":100,"density":0.1}}
- render(elements) — draw on the 10×14 grid using drawing tools
  {"type":"render","elements":[{"type":"fill","color":"#000"},{"type":"heart","cx":5,"cy":7,"size":4,"color":"#FF2266"}]}

  Drawing tools (use as elements inside render):
  - fill(color) — fill entire grid with one color
    {"type":"fill","color":"#000"}
  - text(content,x,y,color) — draw text. Font: 3px wide per char + 1px gap
    {"type":"text","content":"HI","x":2,"y":4,"color":"#FFF"}
  - pixel(x,y,color) — single pixel
    {"type":"pixel","x":5,"y":1,"color":"#F44"}
  - rect(x,y,w,h,color) — filled rectangle
    {"type":"rect","x":0,"y":12,"w":10,"h":2,"color":"#333"}
  - line(x1,y1,x2,y2,color) — line (Bresenham)
    {"type":"line","x1":0,"y1":0,"x2":9,"y2":13,"color":"#FFF"}
  - circle(cx,cy,r,color,fill) — circle. fill=true (default) or false for outline
    {"type":"circle","cx":5,"cy":7,"r":3,"color":"#FFD700","fill":true}
  - triangle(cx,cy,size,direction,color,fill) — triangle. direction: up/down/left/right
    {"type":"triangle","cx":5,"cy":7,"size":4,"direction":"up","color":"#00FF00","fill":true}
  - star(cx,cy,r,color) — 5-pointed star
    {"type":"star","cx":5,"cy":7,"r":3,"color":"#FFD700"}
  - diamond(cx,cy,r,color,fill) — diamond shape
    {"type":"diamond","cx":5,"cy":7,"r":3,"color":"#00BFFF","fill":true}
  - heart(cx,cy,size,color) — heart shape
    {"type":"heart","cx":5,"cy":7,"size":4,"color":"#FF2266"}

  Grid: 10 wide × 14 tall. x=0 left, y=0 top. Center: cx=5, cy=7.
  PREFER shape primitives (heart, star, circle, diamond, triangle) over manual pixels when possible.
  Use pixel only for custom shapes that don't match any primitive.

## Program structure:
{"program":{"name":"...","steps":[{"id":"...","command":{...},"duration":ms_or_null}],"loop":{"count":N,"start_step":"id","end_step":"id"},"on_complete":{"command":{...}}}}
- duration: null = stays forever. milliseconds = auto-advance after that time.
- loop: optional. count=0 means infinite. Repeats from start_step to end_step.
- on_complete: optional. Runs when program finishes all steps/loops.

## Timing: 1min=60000, 5min=300000, 25min=1500000, 1hr=3600000. loop.count 0=infinite.

## Color moods:
Warm/cozy: #FF6B4A #FFE4C4 #D88B70 #FFBF00. Calm: #4A90D9 #008B8B #E6E6FA. Focus: #F0F8FF #ADD8E6. Sleep: #191970 #483D8B. Energy: #FF4444 #FF00FF #FFD700. Nature: #228B22 #8B4513. Romantic: #FFB6C1 #9370DB.

## Examples:

User: "warm and cozy"
{"program":{"name":"Warm Cozy","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#D88B70","color2":"#FFF0DC"}},"duration":null}]}}

User: "show a heart"
{"program":{"name":"Heart","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#1a0a1a"},{"type":"heart","cx":5,"cy":6,"size":4,"color":"#FF2266"}]},"duration":null}]}}

User: "show a star"
{"program":{"name":"Star","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0A0A2E"},{"type":"star","cx":5,"cy":7,"r":4,"color":"#FFD700"}]},"duration":null}]}}

User: "draw a smiley face"
{"program":{"name":"Smiley","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a2a"},{"type":"circle","cx":5,"cy":7,"r":5,"color":"#FFD700","fill":true},{"type":"pixel","x":3,"y":5,"color":"#000"},{"type":"pixel","x":7,"y":5,"color":"#000"},{"type":"pixel","x":3,"y":9,"color":"#000"},{"type":"pixel","x":4,"y":10,"color":"#000"},{"type":"pixel","x":5,"y":10,"color":"#000"},{"type":"pixel","x":6,"y":10,"color":"#000"},{"type":"pixel","x":7,"y":9,"color":"#000"}]},"duration":null}]}}"""


# ── Test prompts (pixel art only) ────────────────────────────────────────
PIXEL_ART_PROMPTS = [
    {"id": 1,  "prompt": "show a star"},
    {"id": 2,  "prompt": "draw a smiley face"},
    {"id": 3,  "prompt": "show an arrow pointing up"},
    {"id": 4,  "prompt": "draw a house"},
    {"id": 5,  "prompt": "show a music note"},
    {"id": 6,  "prompt": "draw a cat face"},
    {"id": 7,  "prompt": "show a sun"},
    {"id": 8,  "prompt": "draw a tree"},
    {"id": 9,  "prompt": "show a lightning bolt"},
    {"id": 10, "prompt": "draw a skull"},
]

# Shape primitives that the renderer supports
SHAPE_TYPES = {"circle", "triangle", "star", "diamond", "heart"}


def query_ollama(prompt: str, system_prompt: str, model: str) -> str | None:
    """Send a prompt to Ollama and return the raw response text."""
    user_msg = f"Create a light program for this request.\n\nRequest: {prompt}\n\nRespond with ONLY a JSON program. No text."
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 4096},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")
    except Exception as e:
        print(f"  OLLAMA ERROR: {e}")
        return None


def extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.rstrip("`").strip()
    text = text.rstrip("\"'")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None

    return None


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
    except Exception:
        return False


def analyze_elements(parsed: dict) -> dict:
    """Analyze what drawing element types are used in a render command."""
    stats = {"total_elements": 0, "primitives_used": [], "pixel_count": 0, "rect_count": 0, "other": []}

    program = parsed.get("program", parsed)
    for step in program.get("steps", []):
        cmd = step.get("command", {})
        if cmd.get("type") == "render":
            for el in cmd.get("elements", []):
                el_type = el.get("type", "")
                stats["total_elements"] += 1
                if el_type in SHAPE_TYPES:
                    stats["primitives_used"].append(el_type)
                elif el_type == "pixel":
                    stats["pixel_count"] += 1
                elif el_type == "rect":
                    stats["rect_count"] += 1
                elif el_type not in ("fill",):
                    stats["other"].append(el_type)

    return stats


def render_grid_ascii(parsed: dict) -> str:
    """Render the output as a simple ASCII grid for visual comparison."""
    grid = [["." for _ in range(10)] for _ in range(14)]

    program = parsed.get("program", parsed)
    for step in program.get("steps", []):
        cmd = step.get("command", {})
        if cmd.get("type") == "render":
            for el in cmd.get("elements", []):
                el_type = el.get("type", "")
                if el_type == "fill":
                    char = " " if el.get("color", "#000") in ("#000", "#000000", "#0a0a1a", "#0A0A2E", "#0a0a2a") else "#"
                    grid = [[char for _ in range(10)] for _ in range(14)]
                elif el_type == "pixel":
                    x, y = el.get("x", 0), el.get("y", 0)
                    if 0 <= x < 10 and 0 <= y < 14:
                        grid[y][x] = "*"
                elif el_type == "rect":
                    x, y, w, h = el.get("x", 0), el.get("y", 0), el.get("w", 1), el.get("h", 1)
                    for ry in range(y, min(y + h, 14)):
                        for rx in range(x, min(x + w, 10)):
                            if 0 <= rx < 10 and 0 <= ry < 14:
                                grid[ry][rx] = "#"
                elif el_type in SHAPE_TYPES:
                    # Mark shape primitives with their first letter
                    char = el_type[0].upper()
                    cx = int(el.get("cx", 5))
                    cy = int(el.get("cy", 7))
                    if 0 <= cx < 10 and 0 <= cy < 14:
                        grid[cy][cx] = char
                    # Fill approximate area
                    r = el.get("r", el.get("size", 3))
                    for dy in range(-r, r + 1):
                        for dx in range(-r, r + 1):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < 10 and 0 <= ny < 14 and grid[ny][nx] in (" ", "."):
                                if abs(dx) + abs(dy) <= r:
                                    grid[ny][nx] = char.lower()
                elif el_type == "line":
                    # Simplified line rendering
                    x1, y1 = el.get("x1", 0), el.get("y1", 0)
                    x2, y2 = el.get("x2", 0), el.get("y2", 0)
                    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
                    for s in range(steps + 1):
                        t = s / steps
                        x = int(x1 + (x2 - x1) * t)
                        y = int(y1 + (y2 - y1) * t)
                        if 0 <= x < 10 and 0 <= y < 14:
                            grid[y][x] = "/"

    lines = []
    lines.append("    " + "".join(str(i) for i in range(10)))
    lines.append("    " + "-" * 10)
    for row_idx, row in enumerate(grid):
        lines.append(f"{row_idx:2d} |" + "".join(row) + "|")
    lines.append("    " + "-" * 10)
    return "\n".join(lines)


def run_test(model: str, system_prompt: str, label: str, prompts: list, send: bool = False, pause: float = 1.0):
    """Run a test suite and return results."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"  Model: {model}")
    print(f"{'=' * 60}\n")

    results = []
    for i, test in enumerate(prompts):
        prompt = test["prompt"]
        print(f"[{i+1:2d}/{len(prompts)}] {prompt}")
        print(f"  Querying {model}...", end="", flush=True)

        t0 = time.time()
        raw = query_ollama(prompt, system_prompt, model)
        elapsed = time.time() - t0

        if raw is None:
            print(f" FAILED ({elapsed:.1f}s)")
            results.append({"id": test["id"], "prompt": prompt, "status": "error", "time": elapsed})
            continue

        print(f" {elapsed:.1f}s")

        parsed = extract_json(raw)
        if parsed is None:
            print(f"  JSON PARSE FAILED: {raw[:150]}...")
            results.append({"id": test["id"], "prompt": prompt, "status": "json_error", "time": elapsed})
            continue

        # Wrap single commands
        if "program" not in parsed and "type" in parsed:
            parsed = {
                "program": {
                    "name": prompt[:30],
                    "steps": [{"id": "main", "command": parsed, "duration": None}],
                }
            }

        stats = analyze_elements(parsed)
        results.append({
            "id": test["id"],
            "prompt": prompt,
            "status": "ok",
            "time": elapsed,
            "stats": stats,
            "program": parsed,
        })

        # Print analysis
        prims = stats["primitives_used"]
        print(f"  Elements: {stats['total_elements']} total | "
              f"Primitives: {prims if prims else 'NONE'} | "
              f"Pixels: {stats['pixel_count']} | Rects: {stats['rect_count']}")

        # ASCII grid preview
        ascii_grid = render_grid_ascii(parsed)
        print(ascii_grid)

        if send:
            ok = send_program(parsed)
            print(f"  -> {'SENT' if ok else 'SEND FAILED'}")

        if i < len(prompts) - 1:
            time.sleep(pause)

        print()

    return results


def print_comparison(results_a: list, results_b: list, label_a: str, label_b: str):
    """Print side-by-side comparison of two test runs."""
    print(f"\n{'=' * 60}")
    print(f"  COMPARISON: {label_a} vs {label_b}")
    print(f"{'=' * 60}\n")

    print(f"{'Prompt':<30s} | {'A: Prims/Px/Rct':>16s} | {'B: Prims/Px/Rct':>16s}")
    print("-" * 70)

    for ra, rb in zip(results_a, results_b):
        prompt = ra["prompt"][:28]

        if ra["status"] == "ok":
            sa = ra["stats"]
            a_str = f"{len(sa['primitives_used']):d}P/{sa['pixel_count']:d}px/{sa['rect_count']:d}r"
        else:
            a_str = ra["status"]

        if rb["status"] == "ok":
            sb = rb["stats"]
            b_str = f"{len(sb['primitives_used']):d}P/{sb['pixel_count']:d}px/{sb['rect_count']:d}r"
        else:
            b_str = rb["status"]

        # Highlight if B uses more primitives
        marker = ""
        if ra["status"] == "ok" and rb["status"] == "ok":
            if len(rb["stats"]["primitives_used"]) > len(ra["stats"]["primitives_used"]):
                marker = " << BETTER"
            elif rb["stats"]["pixel_count"] < ra["stats"]["pixel_count"] and len(rb["stats"]["primitives_used"]) > 0:
                marker = " < fewer px"

        print(f"{prompt:<30s} | {a_str:>16s} | {b_str:>16s}{marker}")

    # Totals
    a_ok = [r for r in results_a if r["status"] == "ok"]
    b_ok = [r for r in results_b if r["status"] == "ok"]
    a_prims = sum(len(r["stats"]["primitives_used"]) for r in a_ok)
    b_prims = sum(len(r["stats"]["primitives_used"]) for r in b_ok)
    a_px = sum(r["stats"]["pixel_count"] for r in a_ok)
    b_px = sum(r["stats"]["pixel_count"] for r in b_ok)

    print("-" * 70)
    print(f"{'TOTALS':<30s} | {a_prims}P/{a_px}px {'':>6s} | {b_prims}P/{b_px}px")
    print(f"{'JSON Valid':<30s} | {len(a_ok)}/{len(results_a)} {'':>10s} | {len(b_ok)}/{len(results_b)}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Test shape primitives vs raw pixels for pixel art")
    parser.add_argument("--model", default="gemma3:4b", help="Base model to test (default: gemma3:4b)")
    parser.add_argument("--also-finetuned", action="store_true", help="Also test lamp-gemma-v2")
    parser.add_argument("--send", action="store_true", help="Send results to lamp server")
    parser.add_argument("--index", type=int, help="Run a single test by index (1-10)")
    parser.add_argument("--pause", type=float, default=1.0, help="Pause between tests (seconds)")
    args = parser.parse_args()

    prompts = PIXEL_ART_PROMPTS
    if args.index:
        prompts = [p for p in prompts if p["id"] == args.index]

    # Test A: Base model + original prompt (no primitives)
    results_a = run_test(
        model=args.model,
        system_prompt=PROMPT_ORIGINAL,
        label=f"A: {args.model} + ORIGINAL prompt (no shape primitives)",
        prompts=prompts,
        send=args.send,
        pause=args.pause,
    )

    # Test B: Base model + enhanced prompt (with primitives)
    results_b = run_test(
        model=args.model,
        system_prompt=PROMPT_WITH_PRIMITIVES,
        label=f"B: {args.model} + ENHANCED prompt (with shape primitives)",
        prompts=prompts,
        send=args.send,
        pause=args.pause,
    )

    # Compare A vs B
    print_comparison(results_a, results_b, "Original", "With Primitives")

    # Optional: Test C — fine-tuned model with enhanced prompt
    results_c = None
    if args.also_finetuned:
        results_c = run_test(
            model="lamp-gemma-v2",
            system_prompt=PROMPT_WITH_PRIMITIVES,
            label="C: lamp-gemma-v2 (fine-tuned) + ENHANCED prompt",
            prompts=prompts,
            send=args.send,
            pause=args.pause,
        )
        print_comparison(results_b, results_c, f"{args.model} + Primitives", "Fine-tuned + Primitives")

    # Save all results
    import os
    results_dir = os.path.join(os.path.dirname(__file__), "..", "benchmark-results2")
    os.makedirs(results_dir, exist_ok=True)

    output = {
        "test": "primitives_comparison",
        "model": args.model,
        "results_original": results_a,
        "results_primitives": results_b,
    }
    if results_c:
        output["results_finetuned_primitives"] = results_c

    out_path = os.path.join(results_dir, "primitives_test_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()

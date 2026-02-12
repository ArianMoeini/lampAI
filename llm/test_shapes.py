"""Test: Tell the model about shape primitives and see if it uses them."""
import json, re, urllib.request, time

OLLAMA_URL = "http://localhost:11434"
LAMP_URL = "http://localhost:3001"
MODEL = "lamp-gemma-v2:latest"

# Updated system prompt with shape primitives
SYSTEM_PROMPT = """You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

## Commands (use inside step.command):
- solid(color) — all LEDs one color
  {"type":"pattern","name":"solid","params":{"color":"#FF4444"}}
- gradient(color, color2) — radial blend
  {"type":"pattern","name":"gradient","params":{"color":"#FF6B4A","color2":"#FFE4C4"}}
- breathing(color, speed) — pulsing glow
  {"type":"pattern","name":"breathing","params":{"color":"#4A90D9","speed":3000}}
- render(elements) — draw on the 10x14 grid using drawing tools:
  - fill(color) — fill entire grid
  - text(content, x, y, color) — draw text. Font: 3px wide per char + 1px gap
  - pixel(x, y, color) — single pixel
  - rect(x, y, w, h, color) — filled rectangle
  - line(x1, y1, x2, y2, color) — line between two points
  - circle(cx, cy, r, color, fill) — circle. fill=true (default) for filled, false for outline
  - triangle(cx, cy, size, direction, color, fill) — triangle. direction: up/down/left/right
  - star(cx, cy, r, color) — 5-pointed star
  - diamond(cx, cy, r, color, fill) — diamond shape
  - heart(cx, cy, size, color) — heart shape
  Grid: 10 wide x 14 tall. x=0 left, y=0 top. Center is roughly (5, 7).

## Program structure:
{"program":{"name":"...","steps":[{"id":"...","command":{...},"duration":ms_or_null}]}}

## Examples:
User: "show a heart"
{"program":{"name":"Heart","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#1a0a1a"},{"type":"heart","cx":5,"cy":6,"size":5,"color":"#FF2266"}]},"duration":null}]}}

User: "draw a star"
{"program":{"name":"Star","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a2a"},{"type":"star","cx":5,"cy":6,"r":4,"color":"#FFD700"}]},"duration":null}]}}"""

TESTS = [
    "show a star",
    "show a sun",
    "draw a stop sign",
    "draw a smiley face",
    "show a christmas tree",
]


def query(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Create a light program for: {prompt}\n\nRespond with ONLY JSON."},
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 4096},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["message"]["content"]


def parse(raw):
    text = re.sub(r"```(?:json)?\s*", "", raw.strip()).rstrip("`").strip()
    start = text.find("{")
    if start < 0: return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try: return json.loads(text[start:i+1])
                except: return None
    return None


def send(program):
    data = json.dumps(program).encode()
    req = urllib.request.Request(
        f"{LAMP_URL}/program", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except:
        return False


print("=" * 60)
print("  SHAPE PRIMITIVES TEST")
print("  Does the model use circle/triangle/star/heart/diamond?")
print("=" * 60)

for prompt in TESTS:
    print(f"\n--- \"{prompt}\" ---")
    print(f"  Querying...", end="", flush=True)
    raw = query(prompt)
    print(f" done")
    print(f"  Raw: {raw[:300]}")

    parsed = parse(raw)
    if parsed:
        if "program" not in parsed and "type" in parsed:
            parsed = {"program": {"name": prompt[:30], "steps": [{"id": "main", "command": parsed, "duration": None}]}}

        # Check if it used shape primitives
        elements = []
        prog = parsed.get("program", parsed)
        for step in prog.get("steps", []):
            cmd = step.get("command", {})
            elements.extend(cmd.get("elements", []))

        types_used = set(el.get("type") for el in elements)
        shape_types = types_used & {"circle", "triangle", "star", "diamond", "heart"}
        if shape_types:
            print(f"  USED SHAPES: {shape_types}")
        else:
            print(f"  No shape primitives used (types: {types_used})")

        ok = send(parsed)
        print(f"  {'SENT' if ok else 'FAILED'} — check emulator")
    else:
        print(f"  PARSE FAILED")

    time.sleep(3)

print("\nDone!")

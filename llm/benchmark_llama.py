"""
Benchmark: Run the same 21 prompts through a LOCAL Ollama model
and send the results to the lamp server.

Usage:
  python3 benchmark_llama.py                        # Llama 3.2, 5s pause
  python3 benchmark_llama.py --model qwen3-vl       # Qwen3-VL 8B
  python3 benchmark_llama.py --fast                  # 2s pause
  python3 benchmark_llama.py --index 5               # Run just one
"""

import json
import time
import re
import sys
import argparse
import urllib.request
import urllib.error

LAMP_SERVER_URL = "http://localhost:3001"
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

# Same system prompt used by the lamp controller
SYSTEM_PROMPT = """You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

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

User: "pomodoro timer 25 min work 5 min break"
{"program":{"name":"Pomodoro","steps":[{"id":"work","command":{"type":"pattern","name":"solid","params":{"color":"#CC3333"}},"duration":1500000},{"id":"break","command":{"type":"pattern","name":"breathing","params":{"color":"#33CC66","speed":4000}},"duration":300000}],"loop":{"count":4,"start_step":"work","end_step":"break"},"on_complete":{"command":{"type":"pattern","name":"rainbow","params":{"speed":2000}}}}}

User: "thunderstorm"
{"program":{"name":"Storm","steps":[{"id":"dark","command":{"type":"pattern","name":"breathing","params":{"color":"#1a1a3a","speed":3000}},"duration":4000},{"id":"flash","command":{"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":300}},"duration":500},{"id":"rumble","command":{"type":"pattern","name":"sparkle","params":{"color":"#4444AA","bgColor":"#0a0a1a","speed":80,"density":0.15}},"duration":3000}],"loop":{"count":0,"start_step":"dark","end_step":"rumble"}}}

User: "clock showing 14:30"
{"program":{"name":"Clock","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a1a"},{"type":"text","content":"14","x":2,"y":2,"color":"#00FF88"},{"type":"pixel","x":5,"y":7,"color":"#00FF88"},{"type":"pixel","x":5,"y":9,"color":"#00FF88"},{"type":"text","content":"30","x":2,"y":9,"color":"#00FF88"}]},"duration":null}]}}

User: "show a heart"
{"program":{"name":"Heart","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#1a0a1a"},{"type":"pixel","x":3,"y":4,"color":"#FF2266"},{"type":"pixel","x":6,"y":4,"color":"#FF2266"},{"type":"rect","x":2,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":5,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":3,"y":7,"w":4,"h":2,"color":"#FF2266"},{"type":"rect","x":4,"y":9,"w":2,"h":1,"color":"#FF2266"}]},"duration":null}]}}"""

# The same 21 prompts from benchmark.py
PROMPTS = [
    # Pixel art (10)
    {"id": 1,  "category": "pixel_art",    "prompt": "show a star"},
    {"id": 2,  "category": "pixel_art",    "prompt": "draw a smiley face"},
    {"id": 3,  "category": "pixel_art",    "prompt": "show an arrow pointing up"},
    {"id": 4,  "category": "pixel_art",    "prompt": "draw a house"},
    {"id": 5,  "category": "pixel_art",    "prompt": "show a music note"},
    {"id": 6,  "category": "pixel_art",    "prompt": "draw a cat face"},
    {"id": 7,  "category": "pixel_art",    "prompt": "show a sun"},
    {"id": 8,  "category": "pixel_art",    "prompt": "draw a tree"},
    {"id": 9,  "category": "pixel_art",    "prompt": "show a lightning bolt"},
    {"id": 10, "category": "pixel_art",    "prompt": "draw a skull"},
    # Analog clock (1)
    {"id": 11, "category": "analog_clock", "prompt": "show an analog clock at 3 o'clock"},
    # Multi-step (10)
    {"id": 12, "category": "multi_step",   "prompt": "be a pomodoro timer"},
    {"id": 13, "category": "multi_step",   "prompt": "simulate a sunrise"},
    {"id": 14, "category": "multi_step",   "prompt": "create a meditation session"},
    {"id": 15, "category": "multi_step",   "prompt": "party mode"},
    {"id": 16, "category": "multi_step",   "prompt": "simulate rain and thunder"},
    {"id": 17, "category": "multi_step",   "prompt": "sleep timer that dims over 30 minutes"},
    {"id": 18, "category": "multi_step",   "prompt": "countdown from 5"},
    {"id": 19, "category": "multi_step",   "prompt": "traffic light sequence"},
    {"id": 20, "category": "multi_step",   "prompt": "romantic evening ambiance"},
    {"id": 21, "category": "multi_step",   "prompt": "weather display showing sunny and 24 degrees"},
]


def query_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str | None:
    """Send a prompt to Ollama and return the raw response text."""
    user_msg = f"Create a light program for this request.\n\nRequest: {prompt}\n\nRespond with ONLY a JSON program. No text."
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
        "options": {"temperature": 0.3},
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
    """Extract JSON from LLM response (same logic as lamp_controller.py)."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.rstrip("`").strip()
    text = text.rstrip("\"'")

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Bracket counting
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Try closing brackets
                    for fix in ["}", "]}", "]}"]:
                        try:
                            return json.loads(candidate + fix)
                        except json.JSONDecodeError:
                            continue
                    return None

    # Unclosed — try adding brackets
    candidate = text[start:]
    missing = candidate.count("{") - candidate.count("}")
    if missing > 0:
        try:
            return json.loads(candidate + "]" + "}" * missing)
        except json.JSONDecodeError:
            try:
                return json.loads(candidate + "}" * missing)
            except json.JSONDecodeError:
                pass
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
    except Exception as e:
        print(f"  SERVER ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Benchmark local Ollama models on lamp prompts")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name (default: llama3.2)")
    parser.add_argument("--fast", action="store_true", help="2s pause instead of 5s")
    parser.add_argument("--index", type=int, help="Run a single test by index (1-21)")
    parser.add_argument("--category", choices=["pixel_art", "analog_clock", "multi_step"])
    args = parser.parse_args()

    model = args.model
    pause = 2 if args.fast else 5
    tests = PROMPTS

    if args.index:
        tests = [t for t in tests if t["id"] == args.index]
    elif args.category:
        tests = [t for t in tests if t["category"] == args.category]

    total = len(tests)
    results = []

    print("=" * 60)
    print(f"  {model.upper()} BENCHMARK — {total} test cases")
    print(f"  Ollama: {OLLAMA_URL} | Server: {LAMP_SERVER_URL}")
    print(f"  Pause between tests: {pause}s")
    print("=" * 60)
    print()

    for i, test in enumerate(tests):
        idx = test["id"]
        cat = test["category"]
        prompt = test["prompt"]

        print(f"[{i+1:2d}/{total}] {cat:14s} | {prompt}")
        print(f"         Querying {model}...", end="", flush=True)

        t0 = time.time()
        raw = query_ollama(prompt, model)
        elapsed = time.time() - t0

        if raw is None:
            print(f" FAILED ({elapsed:.1f}s)")
            results.append({"id": idx, "status": "ollama_error", "prompt": prompt, "time": elapsed})
            continue

        print(f" got response ({elapsed:.1f}s)")

        parsed = extract_json(raw)
        if parsed is None:
            print(f"         JSON PARSE FAILED. Raw: {raw[:200]}")
            results.append({"id": idx, "status": "json_error", "prompt": prompt, "raw": raw[:500], "time": elapsed})
            if i < total - 1:
                time.sleep(pause)
            continue

        # Ensure it's wrapped in a program
        if "program" not in parsed and "type" in parsed:
            parsed = {
                "program": {
                    "name": prompt[:30],
                    "steps": [{"id": "main", "command": parsed, "duration": None}],
                }
            }

        # For multi-step programs with long durations, cap them for visual demo
        program = parsed.get("program", parsed)
        for step in program.get("steps", []):
            if isinstance(step.get("duration"), (int, float)) and step["duration"] > 10000:
                step["duration"] = 3000  # Cap at 3s for demo

        # Cap loop count for demo
        loop = program.get("loop")
        if loop and isinstance(loop.get("count"), int) and (loop["count"] == 0 or loop["count"] > 3):
            loop["count"] = 2

        ok = send_program(parsed)
        status = "OK" if ok else "send_error"
        print(f"         -> {'SENT' if ok else 'SEND FAILED'}")
        results.append({"id": idx, "status": status, "prompt": prompt, "program": parsed, "time": elapsed})

        if i < total - 1:
            print(f"         (waiting {pause}s — check emulator)")
            time.sleep(pause)

    # Summary
    print()
    print("=" * 60)
    print(f"  SUMMARY ({model})")
    print("=" * 60)

    ok_count = 0
    for r in results:
        tag = r["status"].upper()
        symbol = "OK" if tag == "OK" else "FAIL"
        print(f"  [{r['id']:2d}] {symbol:4s} | {r['prompt']}")
        if r.get("raw"):
            print(f"         raw: {r['raw'][:120]}...")
        if tag == "OK":
            ok_count += 1

    print()
    print(f"  {ok_count}/{total} successfully sent to server")

    # Save results to file named after the model
    import os
    safe_name = model.replace(":", "_").replace("/", "_")
    results_dir = os.path.join(os.path.dirname(__file__), "..", "benchmark-results2")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"results_{safe_name}.json")
    with open(out_path, "w") as f:
        json.dump({"model": model, "total": total, "ok": ok_count, "results": results}, f, indent=2)
    print(f"  Results saved to {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Step 7: Evaluate fine-tuned models against the benchmark prompts.

Queries the fine-tuned model via Ollama and measures JSON validity,
schema compliance, and optionally sends programs to the lamp server.

Usage:
    python3 07_evaluate.py --model lamp-llama-3b
    python3 07_evaluate.py --model lamp-gemma-4b --send-to-server
    python3 07_evaluate.py --model lamp-llama-3b --compare-baseline llama3.2
"""

import json
import os
import re
import time
import argparse
import urllib.request
import urllib.error

LAMP_SERVER_URL = "http://localhost:3001"
OLLAMA_URL = "http://localhost:11434"

# The 21 benchmark prompts (held out from training)
BENCHMARK_PROMPTS = [
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
    {"id": 11, "category": "analog_clock", "prompt": "show an analog clock at 3 o'clock"},
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

# System prompt (same as used in training)
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

VALID_PATTERN_NAMES = {"solid", "gradient", "breathing", "wave", "rainbow", "pulse", "sparkle"}
VALID_COMMAND_TYPES = {"pattern", "render", "stop"}
VALID_ELEMENT_TYPES = {"fill", "text", "pixel", "rect", "line"}


def query_ollama(prompt, model):
    """Query Ollama and return raw response text."""
    user_msg = f"Create a light program for this request.\n\nRequest: {prompt}\n\nRespond with ONLY a JSON program. No text."
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 4096},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat", data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")
    except Exception as e:
        return None


def extract_json(text):
    """Extract JSON from LLM response."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.rstrip("`").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    return None

    # Try fixing unclosed brackets
    candidate = text[start:]
    missing = candidate.count("{") - candidate.count("}")
    if missing > 0:
        for fix in ["}" * missing, "]" + "}" * missing]:
            try:
                return json.loads(candidate + fix)
            except json.JSONDecodeError:
                continue
    return None


def validate_program(data):
    """Validate program structure. Returns (is_valid, issues)."""
    issues = []
    if not isinstance(data, dict) or "program" not in data:
        return False, ["not a valid program structure"]

    prog = data["program"]
    if "steps" not in prog or not prog["steps"]:
        return False, ["missing or empty steps"]

    for step in prog["steps"]:
        cmd = step.get("command", {})
        ctype = cmd.get("type")
        if ctype not in VALID_COMMAND_TYPES:
            issues.append(f"invalid command type: {ctype}")
        if ctype == "pattern" and cmd.get("name") not in VALID_PATTERN_NAMES:
            issues.append(f"invalid pattern: {cmd.get('name')}")
        if ctype == "render":
            for elem in cmd.get("elements", []):
                if elem.get("type") not in VALID_ELEMENT_TYPES:
                    issues.append(f"invalid element type: {elem.get('type')}")

    return len(issues) == 0, issues


def send_program(data):
    """Send program to lamp server."""
    try:
        req_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{LAMP_SERVER_URL}/program", data=req_data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned model")
    parser.add_argument("--model", required=True, help="Ollama model name")
    parser.add_argument("--send-to-server", action="store_true", help="Send programs to lamp server")
    parser.add_argument("--pause", type=int, default=3, help="Pause between tests (seconds)")
    args = parser.parse_args()

    results = []
    metrics = {
        "json_valid": 0, "schema_valid": 0, "command_valid": 0,
        "total": len(BENCHMARK_PROMPTS), "times": [],
    }

    print(f"{'='*60}")
    print(f"  EVALUATION: {args.model}")
    print(f"  {len(BENCHMARK_PROMPTS)} benchmark prompts")
    print(f"{'='*60}\n")

    for i, test in enumerate(BENCHMARK_PROMPTS):
        prompt = test["prompt"]
        print(f"[{i+1:2d}/{len(BENCHMARK_PROMPTS)}] {test['category']:14s} | {prompt}")

        t0 = time.time()
        raw = query_ollama(prompt, args.model)
        elapsed = time.time() - t0
        metrics["times"].append(elapsed)

        if raw is None:
            print(f"  -> OLLAMA ERROR ({elapsed:.1f}s)")
            results.append({"id": test["id"], "prompt": prompt, "status": "ollama_error", "time": elapsed})
            continue

        parsed = extract_json(raw)
        if parsed is None:
            print(f"  -> JSON PARSE FAIL ({elapsed:.1f}s)")
            results.append({"id": test["id"], "prompt": prompt, "status": "json_error", "raw": raw[:300], "time": elapsed})
            continue

        metrics["json_valid"] += 1

        # Wrap if needed
        if "program" not in parsed and "type" in parsed:
            parsed = {"program": {"name": prompt[:30], "steps": [{"id": "main", "command": parsed, "duration": None}]}}

        is_valid, issues = validate_program(parsed)
        if is_valid:
            metrics["schema_valid"] += 1
            metrics["command_valid"] += 1

        status = "OK" if is_valid else "schema_error"
        print(f"  -> {status.upper()} ({elapsed:.1f}s)" + (f" {issues}" if issues else ""))

        results.append({
            "id": test["id"], "prompt": prompt, "status": status,
            "program": parsed, "issues": issues, "time": elapsed,
        })

        if args.send_to_server and is_valid:
            # Cap durations for demo
            prog = parsed.get("program", parsed)
            for step in prog.get("steps", []):
                if isinstance(step.get("duration"), (int, float)) and step["duration"] > 10000:
                    step["duration"] = 3000
            loop = prog.get("loop")
            if loop and isinstance(loop.get("count"), int) and (loop["count"] == 0 or loop["count"] > 3):
                loop["count"] = 2
            ok = send_program(parsed)
            print(f"     Server: {'SENT' if ok else 'FAILED'}")

        if i < len(BENCHMARK_PROMPTS) - 1:
            time.sleep(args.pause)

    # Summary
    total = metrics["total"]
    print(f"\n{'='*60}")
    print(f"  RESULTS: {args.model}")
    print(f"{'='*60}")
    print(f"  JSON Valid:    {metrics['json_valid']:2d}/{total} ({metrics['json_valid']/total*100:.0f}%)")
    print(f"  Schema Valid:  {metrics['schema_valid']:2d}/{total} ({metrics['schema_valid']/total*100:.0f}%)")
    print(f"  Command Valid: {metrics['command_valid']:2d}/{total} ({metrics['command_valid']/total*100:.0f}%)")
    if metrics["times"]:
        avg_time = sum(metrics["times"]) / len(metrics["times"])
        print(f"  Avg Time:      {avg_time:.1f}s")

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"eval_{args.model.replace('/', '_')}.json")
    with open(out_path, "w") as f:
        json.dump({"model": args.model, "metrics": metrics, "results": results}, f, indent=2)
    print(f"\n  Saved to: {out_path}")


if __name__ == "__main__":
    main()

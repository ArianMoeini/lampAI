"""
Quick RAG simulation test: inject a closely related Opus-generated example
into the context and see if the model's pixel art improves.
"""

import json
import time
import re
import urllib.request

LAMP_SERVER_URL = "http://localhost:3001"
OLLAMA_URL = "http://localhost:11434"
MODEL = "lamp-gemma-v2:latest"

# The base system prompt (same as benchmark)
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
Warm/cozy: #FF6B4A #FFE4C4 #D88B70 #FFBF00. Calm: #4A90D9 #008B8B #E6E6FA. Focus: #F0F8FF #ADD8E6. Sleep: #191970 #483D8B. Energy: #FF4444 #FF00FF #FFD700. Nature: #228B22 #8B4513. Romantic: #FFB6C1 #9370DB."""

# Opus-generated "similar" examples with perfect pixel coordinates.
# Each maps: test prompt -> (similar_prompt, similar_response)
# The similar example is close but NOT the same object.
RAG_EXAMPLES = {
    "show a star": {
        "similar_prompt": "show a diamond",
        "similar_response": '{"program":{"name":"Diamond","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a2a"},{"type":"pixel","x":5,"y":1,"color":"#00FFAA"},{"type":"pixel","x":4,"y":2,"color":"#00FFAA"},{"type":"pixel","x":6,"y":2,"color":"#00FFAA"},{"type":"pixel","x":3,"y":3,"color":"#00FFAA"},{"type":"pixel","x":7,"y":3,"color":"#00FFAA"},{"type":"pixel","x":2,"y":4,"color":"#00FFAA"},{"type":"pixel","x":8,"y":4,"color":"#00FFAA"},{"type":"pixel","x":2,"y":5,"color":"#00FFAA"},{"type":"pixel","x":8,"y":5,"color":"#00FFAA"},{"type":"pixel","x":2,"y":6,"color":"#00FFAA"},{"type":"pixel","x":8,"y":6,"color":"#00FFAA"},{"type":"pixel","x":3,"y":7,"color":"#00FFAA"},{"type":"pixel","x":7,"y":7,"color":"#00FFAA"},{"type":"pixel","x":4,"y":8,"color":"#00FFAA"},{"type":"pixel","x":6,"y":8,"color":"#00FFAA"},{"type":"pixel","x":5,"y":9,"color":"#00FFAA"}]},"duration":null}]}}'
    },
    "show a sun": {
        "similar_prompt": "show a flower",
        "similar_response": '{"program":{"name":"Flower","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a1a0a"},{"type":"pixel","x":5,"y":2,"color":"#FF69B4"},{"type":"pixel","x":3,"y":3,"color":"#FF69B4"},{"type":"pixel","x":7,"y":3,"color":"#FF69B4"},{"type":"pixel","x":4,"y":4,"color":"#FFD700"},{"type":"pixel","x":5,"y":4,"color":"#FFD700"},{"type":"pixel","x":6,"y":4,"color":"#FFD700"},{"type":"pixel","x":3,"y":5,"color":"#FF69B4"},{"type":"pixel","x":4,"y":5,"color":"#FFD700"},{"type":"pixel","x":5,"y":5,"color":"#FFD700"},{"type":"pixel","x":6,"y":5,"color":"#FFD700"},{"type":"pixel","x":7,"y":5,"color":"#FF69B4"},{"type":"pixel","x":4,"y":6,"color":"#FFD700"},{"type":"pixel","x":5,"y":6,"color":"#FFD700"},{"type":"pixel","x":6,"y":6,"color":"#FFD700"},{"type":"pixel","x":5,"y":7,"color":"#FF69B4"},{"type":"pixel","x":5,"y":8,"color":"#228B22"},{"type":"pixel","x":5,"y":9,"color":"#228B22"},{"type":"pixel","x":5,"y":10,"color":"#228B22"},{"type":"pixel","x":4,"y":10,"color":"#228B22"},{"type":"pixel","x":6,"y":9,"color":"#228B22"}]},"duration":null}]}}'
    },
    "draw a smiley face": {
        "similar_prompt": "draw a sad face",
        "similar_response": '{"program":{"name":"Sad Face","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a2a"},{"type":"pixel","x":3,"y":3,"color":"#FFD700"},{"type":"pixel","x":4,"y":3,"color":"#FFD700"},{"type":"pixel","x":6,"y":3,"color":"#FFD700"},{"type":"pixel","x":7,"y":3,"color":"#FFD700"},{"type":"pixel","x":3,"y":4,"color":"#FFD700"},{"type":"pixel","x":4,"y":4,"color":"#FFD700"},{"type":"pixel","x":6,"y":4,"color":"#FFD700"},{"type":"pixel","x":7,"y":4,"color":"#FFD700"},{"type":"pixel","x":2,"y":2,"color":"#FFD700"},{"type":"pixel","x":3,"y":2,"color":"#FFD700"},{"type":"pixel","x":7,"y":2,"color":"#FFD700"},{"type":"pixel","x":8,"y":2,"color":"#FFD700"},{"type":"pixel","x":4,"y":10,"color":"#FFD700"},{"type":"pixel","x":5,"y":10,"color":"#FFD700"},{"type":"pixel","x":6,"y":10,"color":"#FFD700"},{"type":"pixel","x":3,"y":9,"color":"#FFD700"},{"type":"pixel","x":7,"y":9,"color":"#FFD700"}]},"duration":null}]}}'
    },
    "draw a house": {
        "similar_prompt": "draw a castle tower",
        "similar_response": '{"program":{"name":"Castle Tower","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a2a"},{"type":"pixel","x":3,"y":1,"color":"#888"},{"type":"pixel","x":5,"y":1,"color":"#888"},{"type":"pixel","x":7,"y":1,"color":"#888"},{"type":"rect","x":3,"y":2,"w":5,"h":2,"color":"#888"},{"type":"rect","x":4,"y":4,"w":3,"h":6,"color":"#AAA"},{"type":"rect","x":5,"y":8,"w":1,"h":2,"color":"#654321"},{"type":"pixel","x":5,"y":5,"color":"#87CEEB"},{"type":"pixel","x":5,"y":6,"color":"#87CEEB"}]},"duration":null}]}}'
    },
    "weather display showing sunny and 24 degrees": {
        "similar_prompt": "weather display showing cloudy and 18 degrees",
        "similar_response": '{"program":{"name":"Cloudy 18","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#4a4a5a"},{"type":"pixel","x":4,"y":2,"color":"#CCC"},{"type":"pixel","x":5,"y":2,"color":"#CCC"},{"type":"pixel","x":6,"y":2,"color":"#CCC"},{"type":"pixel","x":3,"y":3,"color":"#DDD"},{"type":"pixel","x":4,"y":3,"color":"#DDD"},{"type":"pixel","x":5,"y":3,"color":"#DDD"},{"type":"pixel","x":6,"y":3,"color":"#DDD"},{"type":"pixel","x":7,"y":3,"color":"#DDD"},{"type":"pixel","x":3,"y":4,"color":"#CCC"},{"type":"pixel","x":4,"y":4,"color":"#CCC"},{"type":"pixel","x":5,"y":4,"color":"#CCC"},{"type":"pixel","x":6,"y":4,"color":"#CCC"},{"type":"pixel","x":7,"y":4,"color":"#CCC"},{"type":"text","content":"18","x":2,"y":9,"color":"#FFFFFF"}]},"duration":null}]}}'
    },
}

# Tests to run (subset of pixel art + the weather one)
TESTS = [
    {"id": 1,  "prompt": "show a star"},
    {"id": 2,  "prompt": "draw a smiley face"},
    {"id": 4,  "prompt": "draw a house"},
    {"id": 7,  "prompt": "show a sun"},
    {"id": 21, "prompt": "weather display showing sunny and 24 degrees"},
]


def query_ollama(prompt: str, rag_example: dict | None = None) -> str | None:
    """Send a prompt to Ollama, optionally with a RAG-injected example."""
    if rag_example:
        user_msg = (
            f'Here is a similar example for reference:\n'
            f'User: "{rag_example["similar_prompt"]}"\n'
            f'Response: {rag_example["similar_response"]}\n\n'
            f'Now create a light program for this request.\n\n'
            f'Request: {prompt}\n\n'
            f'Respond with ONLY a JSON program. No text.'
        )
    else:
        user_msg = f"Create a light program for this request.\n\nRequest: {prompt}\n\nRespond with ONLY a JSON program. No text."

    payload = {
        "model": MODEL,
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
            f"{OLLAMA_URL}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def extract_json(text: str) -> dict | None:
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
    return None


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
    print("=" * 60)
    print("  RAG SIMULATION TEST")
    print("  Model:", MODEL)
    print("  Testing: baseline vs RAG-augmented")
    print("=" * 60)
    print()

    for test in TESTS:
        prompt = test["prompt"]
        rag_ex = RAG_EXAMPLES.get(prompt)

        print(f"--- Test #{test['id']}: \"{prompt}\" ---")

        # A) Baseline (no RAG)
        print(f"  [A] Baseline (no example)...", end="", flush=True)
        raw_a = query_ollama(prompt, rag_example=None)
        parsed_a = extract_json(raw_a) if raw_a else None
        if parsed_a:
            if "program" not in parsed_a and "type" in parsed_a:
                parsed_a = {"program": {"name": prompt[:30], "steps": [{"id": "main", "command": parsed_a, "duration": None}]}}
            print(" OK")
        else:
            print(" FAILED")

        # Send baseline to emulator
        if parsed_a:
            send_program(parsed_a)
            print("  [A] SENT — check emulator (3s)...")
            time.sleep(3)

        # B) RAG-augmented
        if rag_ex:
            print(f"  [B] With RAG example (\"{rag_ex['similar_prompt']}\")...", end="", flush=True)
            raw_b = query_ollama(prompt, rag_example=rag_ex)
            parsed_b = extract_json(raw_b) if raw_b else None
            if parsed_b:
                if "program" not in parsed_b and "type" in parsed_b:
                    parsed_b = {"program": {"name": prompt[:30], "steps": [{"id": "main", "command": parsed_b, "duration": None}]}}
                print(" OK")
            else:
                print(" FAILED")

            if parsed_b:
                send_program(parsed_b)
                print("  [B] SENT — check emulator (3s)...")
                time.sleep(3)
        else:
            print("  [B] No RAG example defined, skipping")

        print()

    print("Done! Compare the visual quality of A vs B for each test.")


if __name__ == "__main__":
    main()

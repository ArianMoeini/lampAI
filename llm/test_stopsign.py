"""Test RAG for stop sign: inject a similar 'warning sign' example, then query."""
import json, re, urllib.request, time

OLLAMA_URL = "http://localhost:11434"
LAMP_URL = "http://localhost:3001"
MODEL = "lamp-gemma-v2:latest"

SYSTEM_PROMPT = """You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

## Commands (use inside step.command):
- solid(color) — all LEDs one color
  {"type":"pattern","name":"solid","params":{"color":"#FF4444"}}
- gradient(color, color2) — radial blend, center to edge
  {"type":"pattern","name":"gradient","params":{"color":"#FF6B4A","color2":"#FFE4C4"}}
- breathing(color, speed) — pulsing glow. speed in ms (2000=calm, 500=urgent)
  {"type":"pattern","name":"breathing","params":{"color":"#4A90D9","speed":3000}}
- render(elements) — draw on the 10×14 grid using drawing tools
  {"type":"render","elements":[{"type":"fill","color":"#000"},{"type":"text","content":"HI","x":2,"y":4,"color":"#FFF"},{"type":"pixel","x":5,"y":1,"color":"#F44"},{"type":"rect","x":0,"y":12,"w":10,"h":2,"color":"#333"}]}
  Drawing tools: fill(color), text(content,x,y,color), pixel(x,y,color), rect(x,y,w,h,color), line(x1,y1,x2,y2,color)
  Grid: 10 wide × 14 tall. x=0 left, y=0 top. Text font: 3px wide per char + 1px gap. Use pixel for custom shapes.

## Program structure:
{"program":{"name":"...","steps":[{"id":"...","command":{...},"duration":ms_or_null}]}}
- duration: null = stays forever."""

# Opus-crafted RAG example: a "yield sign" (triangle with text)
# This teaches the model how to build a geometric sign shape with pixels
RAG_EXAMPLE_PROMPT = "show a go sign"
RAG_EXAMPLE_RESPONSE = json.dumps({"program":{"name":"Go Sign","steps":[{"id":"show","command":{"type":"render","elements":[
    {"type":"fill","color":"#1a1a1a"},
    # Green filled rounded sign body
    {"type":"rect","x":2,"y":2,"w":6,"h":7,"color":"#008800"},
    {"type":"pixel","x":1,"y":3,"color":"#008800"},
    {"type":"pixel","x":8,"y":3,"color":"#008800"},
    {"type":"pixel","x":1,"y":4,"color":"#008800"},
    {"type":"pixel","x":8,"y":4,"color":"#008800"},
    {"type":"pixel","x":1,"y":5,"color":"#008800"},
    {"type":"pixel","x":8,"y":5,"color":"#008800"},
    {"type":"pixel","x":1,"y":6,"color":"#008800"},
    {"type":"pixel","x":8,"y":6,"color":"#008800"},
    {"type":"pixel","x":1,"y":7,"color":"#008800"},
    {"type":"pixel","x":8,"y":7,"color":"#008800"},
    # "GO" text centered on the sign
    {"type":"text","content":"GO","x":2,"y":4,"color":"#FFFFFF"},
    # Post
    {"type":"rect","x":4,"y":10,"w":2,"h":3,"color":"#888888"},
]},"duration":None}]}})

# The actual request
PROMPT = "show a traffic stop sign"

user_msg = (
    f'Here is a similar example for reference:\n'
    f'User: "{RAG_EXAMPLE_PROMPT}"\n'
    f'Response: {RAG_EXAMPLE_RESPONSE}\n\n'
    f'Now create a light program for this request.\n\n'
    f'Request: {PROMPT}\n\n'
    f'Respond with ONLY a JSON program. No text.'
)

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ],
    "stream": False,
    "options": {"temperature": 0.3, "num_predict": 4096},
}

print(f"Querying {MODEL} with RAG example (yield sign -> stop sign)...")
data = json.dumps(payload).encode()
req = urllib.request.Request(
    f"{OLLAMA_URL}/api/chat", data=data,
    headers={"Content-Type": "application/json"}, method="POST"
)
with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read())
    raw = result["message"]["content"]

print(f"Raw response:\n{raw}\n")

# Parse JSON
text = re.sub(r"```(?:json)?\s*", "", raw.strip()).rstrip("`").strip()
start = text.find("{")
parsed = None
if start >= 0:
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    pass
                break

if parsed:
    if "program" not in parsed and "type" in parsed:
        parsed = {"program": {"name": "stop sign", "steps": [{"id": "main", "command": parsed, "duration": None}]}}
    data = json.dumps(parsed).encode()
    req = urllib.request.Request(
        f"{LAMP_URL}/program", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    print("SENT to emulator — check it!")
else:
    print("FAILED to parse JSON")

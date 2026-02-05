# AI-Controlled Lamp System Architecture

## The Core Insight: The LLM Writes Programs Dynamically

**No fine-tuning needed.** LLMs already understand colors, Pomodoro timers, sunsets, moods. What they need is:
1. Knowledge of the lamp's API (what commands exist)
2. A structured output format (the program schema)

The LLM **generates a unique program from scratch for every request**. There are no pre-written programs. The schema is like a grammar - it defines the structure (steps, durations, loops, commands), but the LLM fills in the creative content (which colors, which patterns, how many steps, what timing) based on what the user asks for.

Think of it like HTML: the LLM knows the tags (`<div>`, `<p>`), but writes completely different pages every time. Same here - the LLM knows the building blocks (`solid`, `breathing`, `gradient`, durations, loops) and composes them into novel programs for each request.

---

## How the Schema Maps to the Real Lamp

The lamp has **172 individually addressable LEDs**: a 10x14 front display (IDs 0-139) and 32 ambient back LEDs (IDs 140-171). The existing server already accepts these commands:

| Server Endpoint | What It Does | Schema `command` Equivalent |
|---|---|---|
| `POST /pattern` `{name:"solid", params:{color}}` | All LEDs one color | `{"type":"pattern","name":"solid","params":{"color":"#FF4444"}}` |
| `POST /pattern` `{name:"gradient", params:{color,color2}}` | Radial gradient center→edge | `{"type":"pattern","name":"gradient","params":{"color":"#FF6B4A","color2":"#FFE4C4"}}` |
| `POST /pattern` `{name:"breathing", params:{color,speed}}` | Pulsing brightness | `{"type":"pattern","name":"breathing","params":{"color":"#4A90D9","speed":4000}}` |
| `POST /pattern` `{name:"wave", params:{color,color2,speed}}` | Color ripple across rows | `{"type":"pattern","name":"wave","params":{"color":"#FF6B4A","color2":"#FFE4C4","speed":2000}}` |
| `POST /pattern` `{name:"rainbow", params:{speed}}` | Cycling rainbow | `{"type":"pattern","name":"rainbow","params":{"speed":3000}}` |
| `POST /pattern` `{name:"pulse", params:{color,speed}}` | Quick flash then fade (one-shot) | `{"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":500}}` |
| `POST /pattern` `{name:"sparkle", params:{color,bgColor,speed,density}}` | Random twinkling | `{"type":"pattern","name":"sparkle","params":{"color":"#FFF","bgColor":"#1a1a1a","speed":100,"density":0.1}}` |
| `POST /led/:id` `{color}` | Set one LED | `{"type":"led","id":42,"color":"#FF0000"}` |
| `POST /leds` `{leds:[{id,color},...]}` | Set multiple LEDs | `{"type":"bulk","leds":[{"id":0,"color":"#FF0000"},...]}` |
| `POST /stop` | Stop animation | `{"type":"stop"}` |

**Every `command` in the program schema IS the exact JSON the server already understands.** The program schema adds nothing new at the LED level — it only adds **time** (durations, loops, sequences) on top.

### What the schema CAN express for this lamp:
- Any of the 7 animated patterns with any colors/speeds
- Static scenes (gradient, solid) that stay indefinitely (`duration: null`)
- Timed sequences (red for 25min → green for 5min → repeat)
- One-shot effects (pulse flash between steps)
- Loops (repeat a range of steps N times)
- Individual pixel control (for advanced effects like text/icons on the 10x14 grid)

### Current limitations (fine for v1, expandable later):
- Can't run two patterns simultaneously (front + back independently) — each step is one command
- Transitions between steps are instant or fade — no crossfade of two patterns overlapping
- No "reactive" steps (e.g., "speed up if music is loud") — that's Phase 3 territory

---

## How the LLM Interprets Vague Requests

### The Problem
A 3B model needs to turn `"I want something cozy for studying"` into valid multi-step JSON. The current prompt has **zero examples** and a fragile JSON parser. That won't work.

### The Solution: Structured Prompt with Few-Shot Examples

The system prompt will be ~1200 tokens (leaving room for input/output on a 3B model) and structured as:

**Section 1 — Role (30 tokens):**
> You are a lamp programmer. Output ONLY a JSON program. No text.

**Section 2 — Command Reference (200 tokens):**
Compact list of all 7 patterns with their params. One line each:
> `gradient(color, color2)` — radial blend, center to edge
> `breathing(color, speed)` — pulsing glow, speed in ms (2000=calm, 500=urgent)
> etc.

**Section 3 — Program Structure (100 tokens):**
> Programs have: steps (id, command, duration_ms or null), optional loop, optional on_complete

**Section 4 — Three Few-Shot Examples (~700 tokens):**

These three examples teach the model the full range — from trivial to complex:

**Example A — Simple mood (teaches: single step, null duration, gradient)**
> User: "warm and cozy"
> ```json
> {"program":{"name":"Warm Cozy","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#D88B70","color2":"#FFF0DC"}},"duration":null}]}}
> ```

**Example B — Timed activity (teaches: 2 steps, durations, loop)**
> User: "pomodoro timer 25 min work 5 min break"
> ```json
> {"program":{"name":"Pomodoro","steps":[{"id":"work","command":{"type":"pattern","name":"solid","params":{"color":"#CC3333"}},"duration":1500000},{"id":"break","command":{"type":"pattern","name":"breathing","params":{"color":"#33CC66","speed":4000}},"duration":300000}],"loop":{"count":4,"start_step":"work","end_step":"break"}}}
> ```

**Example C — Creative/atmospheric (teaches: multi-step composition, sparkle + breathing)**
> User: "thunderstorm"
> ```json
> {"program":{"name":"Storm","steps":[{"id":"dark","command":{"type":"pattern","name":"breathing","params":{"color":"#1a1a3a","speed":3000}},"duration":4000},{"id":"flash","command":{"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":300}},"duration":500},{"id":"rumble","command":{"type":"pattern","name":"sparkle","params":{"color":"#4444AA","bgColor":"#0a0a1a","speed":80,"density":0.15}},"duration":3000}],"loop":{"count":0,"start_step":"dark","end_step":"rumble"}}}
> ```

**Section 5 — Timing Cheat Sheet (50 tokens):**
> 1min=60000, 5min=300000, 25min=1500000, 1hr=3600000. `loop.count: 0` = infinite.

**Section 6 — Color Moods (100 tokens):**
> Warm/cozy: #FF6B4A, #FFE4C4, #FFBF00. Calm: #4A90D9, #008B8B. Focus: #F0F8FF, #ADD8E6. Sleep: #191970. Energy: #FF4444, #FFD700.

### Why 3 examples are enough for a 3B model
The examples cover the three main "shapes" of requests:
1. **Static mood** → 1 step, no duration → model generalizes to any mood/color
2. **Timed routine** → N steps with ms durations, loop → model generalizes to any timer/routine
3. **Creative scene** → multi-step composition of different patterns → model generalizes to atmospheric requests

A 3B model excels at pattern matching from examples. It doesn't need to "understand" the schema abstractly — it sees the pattern in the examples and fills in new content. If the output quality isn't good enough, we can bump to Llama 3.2 8B (still fits in 16GB RAM with Q4 quantization at ~6-7GB).

### Robust JSON Parsing (fixing current weakness)
The current parser uses `\{[^{}]*\}` regex which **breaks on nested JSON**. Programs have nested objects/arrays. New approach:
1. Strip markdown fences and surrounding text
2. Find the outermost `{` and its matching `}` using bracket counting
3. `json.loads()` the extracted string
4. Validate against schema: must have `program.steps`, each step must have `id` and `command`
5. If validation fails, wrap raw command in a single-step program (backwards compat)

---

## Architecture Overview

```
Voice/Text Input
       |
       v
[Speech-to-Text] (whisper.cpp on Pi)
       |
       v
[LLM] (Llama 3.2 3B via Ollama, on Pi)
  + system prompt with program schema & few-shot examples
       |
       v
Light Program JSON (multi-step sequence with timing)
       |
       v
[ProgramScheduler] (new component in Node.js server)
  executes steps, manages timers, handles loops/transitions
       |
       v
[Existing Server API] (unchanged pattern engine + LED controller)
       |               |
       v               v
  Physical LEDs    Browser Emulator
  (SPI/GPIO)       (WebSocket)
```

---

## New Components to Build

### 1. Light Program Schema (the LLM's output format)

Simple request ("make it warm") → single-step program:
```json
{
  "program": {
    "name": "Warm Cozy",
    "steps": [{
      "id": "main",
      "command": {"type": "pattern", "name": "gradient", "params": {"color": "#FF6B4A", "color2": "#FFE4C4"}},
      "duration": null
    }]
  }
}
```

Complex request ("Pomodoro timer") → multi-step program:
```json
{
  "program": {
    "name": "Pomodoro Timer",
    "steps": [
      {"id": "work", "command": {"type": "pattern", "name": "solid", "params": {"color": "#FF4444"}}, "duration": 1500000},
      {"id": "work_done", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFFFFF", "speed": 500}}, "duration": 3000},
      {"id": "break", "command": {"type": "pattern", "name": "breathing", "params": {"color": "#44FF44", "speed": 4000}}, "duration": 300000, "transition": {"type": "fade", "duration": 2000}},
      {"id": "break_done", "command": {"type": "pattern", "name": "pulse", "params": {"color": "#FFD700", "speed": 300}}, "duration": 2000}
    ],
    "loop": {"count": 4, "start_step": "work", "end_step": "break_done"},
    "on_complete": {"command": {"type": "pattern", "name": "rainbow", "params": {"speed": 2000}}},
    "on_cancel": {"command": {"type": "pattern", "name": "breathing", "params": {"color": "#FFE4C4", "speed": 3000}}}
  }
}
```

Key: every `command` inside a step is the **exact same JSON** the server already accepts. Zero changes to existing patterns or LED controller.

### 2. ProgramScheduler (`lamp/server/scheduler.js`) - NEW FILE

Runs inside the Node.js server process. Responsibilities:
- Parse and validate light programs
- Execute steps sequentially with proper timing (`setTimeout`)
- Handle loops (repeat step ranges N times)
- Handle transitions (fade between steps using LED color interpolation)
- Track state: current step, elapsed time, loop iteration
- Broadcast progress to WebSocket clients
- Support pause/resume/cancel

New API endpoints added to `server.js`:
- `POST /program` - submit a light program
- `GET /program/status` - current step, progress, time remaining
- `POST /program/pause` / `POST /program/resume` / `POST /program/cancel`

### 3. Updated System Prompt (`lamp/llm/prompts.py`) - REWRITE

The prompt teaches the LLM to output programs instead of single commands. Structured as:
1. Role definition ("you are a lighting programmer")
2. Compact program schema reference
3. Available lamp commands (existing list)
4. Timing reference (1 min = 60000ms, etc.)
5. Color psychology (existing)
6. **3 few-shot examples** (simple, medium, complex) - critical for small models

Must stay under ~1200 tokens total to leave room for input/output on a 3B model.

### 4. Updated LLM Controller (`lamp/llm/lamp_controller.py`) - MODIFY

- Add `send_program()` method (POST to `/program`)
- Fix JSON parser: bracket-counting extraction instead of regex
- Add schema validation
- Wrap single-command outputs in a program automatically (backwards compatibility)
- Add program control methods (pause, resume, cancel, status)

### 5. Voice Input Pipeline - NEW (Phase 2)

```
Microphone → whisper.cpp (on Pi) → text → LLM → program → scheduler
```

Using whisper.cpp (C++ implementation) for speech-to-text on the Pi. The 16GB Pi can run whisper-tiny or whisper-base comfortably alongside Ollama.

### 6. Physical LED Driver - NEW (Phase 2)

SPI/GPIO output from the Pi to drive WS2812B/NeoPixel LEDs. Add a new module `lamp/server/gpio-driver.js` that:
- Subscribes to LED state changes from `LedController`
- Writes color data to the LED strip via SPI using `rpi-ws281x` or similar Node.js library
- Maps the 172 virtual LEDs to physical LED positions

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `lamp/server/scheduler.js` | CREATE | ProgramScheduler class |
| `lamp/server/server.js` | MODIFY | Add /program endpoints, scheduler integration |
| `lamp/llm/prompts.py` | REWRITE | Program-aware system prompt with few-shot examples |
| `lamp/llm/lamp_controller.py` | MODIFY | Add send_program(), fix JSON parser, add validation |
| `lamp/server/gpio-driver.js` | CREATE | Physical LED SPI output (Phase 2) |
| `lamp/voice/voice_input.py` | CREATE | Whisper.cpp speech-to-text pipeline (Phase 2) |
| `lamp/vision/vision_controller.py` | CREATE | Hailo NPU ambient/presence detection (Phase 3) |

---

## Implementation Phases

### Phase 1: Core Program System (local Mac testing)
1. Create `scheduler.js` with ProgramScheduler
2. Add `/program` endpoints to `server.js`
3. Rewrite `prompts.py` with program-aware prompt
4. Update `lamp_controller.py` to send programs + fix JSON parser
5. Test: curl programs through emulator
6. Test: LLM generates programs from natural language via Ollama

### Phase 2: Physical Hardware (on Raspberry Pi)
7. Wire WS2812B LEDs to Pi SPI
8. Create `gpio-driver.js` LED output
9. Add whisper.cpp voice input pipeline
10. Test end-to-end: voice → LLM → scheduler → physical LEDs

### Phase 3: Vision & Polish (Optional)
11. Hailo NPU ambient light detection
12. Presence-based auto behaviors
13. Program library (save/load named programs)
14. Emulator UI for program status display

---

## Resource Budget on 16GB Pi

| Component | RAM | Notes |
|-----------|-----|-------|
| Ollama + Llama 3.2 3B (Q4) | ~4-5GB | Main LLM inference |
| whisper.cpp (tiny/base) | ~200MB | Speech-to-text |
| Node.js server + scheduler | ~100MB | LED control + scheduling |
| Python controller | ~50MB | LLM client |
| OS + overhead | ~1.5GB | Raspberry Pi OS |
| **Total** | **~6-7GB** | Comfortable within 16GB |

---

## Verification Plan

After Phase 1 implementation:
1. Start the Node.js server (`node server.js`)
2. Open emulator in browser (`http://localhost:3001` or static serve)
3. Run: `curl -X POST http://localhost:3001/program -H "Content-Type: application/json" -d '{"program":{"name":"Test","steps":[{"id":"red","command":{"type":"pattern","name":"solid","params":{"color":"#FF0000"}},"duration":3000},{"id":"blue","command":{"type":"pattern","name":"solid","params":{"color":"#0000FF"}},"duration":3000}],"loop":{"count":2,"start_step":"red","end_step":"blue"}}}'`
4. Verify emulator shows red for 3s → blue for 3s → red for 3s → blue for 3s
5. Run: `python lamp_controller.py --command "be a pomodoro timer"`
6. Verify LLM outputs a multi-step program with work/break phases
7. Check `GET /program/status` returns current step and timing info

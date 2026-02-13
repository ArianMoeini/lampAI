# Decision: Multi-Step Program Scheduler

**Date:** 2026-02-05
**Commits:** 702f44a ("finished first step"), 1adab7f ("solved")
**Status:** Complete

## Problem

The initial system could only execute single commands ("turn on red"). Real lamp experiences require **timed sequences** — a thunderstorm needs dark sky → lightning flash → rain sparkle cycling continuously. A Pomodoro timer needs 25min red → 5min green → repeat 4x.

## Solution

Added `ProgramScheduler` class (`server/scheduler.js`) that executes JSON programs with steps, durations, and loops.

### Program Structure

```json
{
  "program": {
    "name": "Thunderstorm",
    "steps": [
      {"id": "dark", "command": {"type": "pattern", "name": "breathing", ...}, "duration": 4000},
      {"id": "flash", "command": {"type": "pattern", "name": "pulse", ...}, "duration": 500},
      {"id": "rumble", "command": {"type": "pattern", "name": "sparkle", ...}, "duration": 3000}
    ],
    "loop": {"count": 0, "start_step": "dark", "end_step": "rumble"},
    "on_complete": {"command": {"type": "pattern", "name": "solid", ...}}
  }
}
```

### Key Design Choices

- **`duration: null`** = step stays forever (no auto-advance). Used for static scenes.
- **`duration: ms`** = auto-advance after that many milliseconds. Used for animations.
- **`loop.count: 0`** = infinite loop. Used for ambient effects.
- **`on_complete`** = runs when all loops finish. Used for "done" signals.
- **Step IDs** = string identifiers for loop references. Validated at start time.

### Updated System Prompt

The LLM system prompt (`llm/prompts.py`) was expanded with:
- Program structure documentation
- Timing reference (1min=60000, 5min=300000, etc.)
- 3 few-shot examples: Warm Cozy (static), Pomodoro (timed loops), Thunderstorm (infinite loop)
- Color mood reference for creative choices

## API Endpoints Added

- `POST /program` — Submit a light program
- `GET /program/status` — Current step, elapsed time
- `POST /program/pause`, `/resume`, `/cancel` — Playback control

## Files Changed

- **New:** `server/scheduler.js` (329 lines) — ProgramScheduler class
- **Modified:** `server/server.js` — Program API endpoints
- **Modified:** `llm/prompts.py` — Program-aware system prompt with examples
- **Modified:** `llm/lamp_controller.py` — `send_program()` method

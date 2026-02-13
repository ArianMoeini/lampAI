# Decision: Project Foundation — Moonside Lamp Emulator

**Date:** 2026-02-03
**Commit:** 5b94ebe ("fixed it")
**Status:** Complete

## Problem

Build a 172-LED lamp (10x14 front grid + 32 ambient back LEDs) controlled by natural language through local LLMs. The physical lamp doesn't exist yet — need a browser-based emulator to develop and test the software stack before hardware deployment.

## Solution

Three-layer architecture:

```
Browser Emulator (HTML5 Canvas)
    ↕ WebSocket (real-time)
Node.js Control Server (Express)
    ↕ HTTP API
Python LLM Controller (Ollama)
```

### Layer 1: Emulator (`emulator/`)
- HTML5 Canvas rendering 172 LEDs with realistic glow effects
- WebSocket client for real-time state updates
- Frosted glass overlay + ambient glow simulation
- Responsive layout with decorative knobs

### Layer 2: Server (`server/`)
- Express + WebSocket server on port 3001
- `LedController` — state management for 172 LEDs
- `PatternEngine` — 7 animated patterns (solid, gradient, breathing, wave, rainbow, pulse, sparkle)
- REST API: `/solid`, `/gradient`, `/pattern`, `/stop`, `/state`

### Layer 3: LLM (`llm/`)
- `lamp_controller.py` — Ollama client that translates natural language to LED commands
- `prompts.py` — System prompt teaching the LLM about lamp commands
- JSON extraction with bracket-counting parser

## Why This Stack?

- **Node.js server**: Real-time WebSocket support, runs well on Raspberry Pi
- **Python LLM layer**: Ollama has the best Python client, easy to swap models
- **HTML5 Canvas emulator**: No hardware needed for development; can test visual output instantly
- **Local LLMs via Ollama**: Privacy-first, no cloud dependency, runs on Pi 5

## Files Created

- `emulator/index.html`, `lamp.js`, `styles.css`, `websocket-client.js`
- `server/server.js`, `led-controller.js`, `patterns.js`, `package.json`
- `llm/lamp_controller.py`, `prompts.py`, `requirements.txt`
- `README.md`

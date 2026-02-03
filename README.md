# Moonside Lamp Emulator

A digital twin of the Moonside Neon Crystal Cube lamp, controllable via a local LLM.

## Architecture

```
[Local LLM (Ollama)] → [Control Server (Node.js)] → [Web Emulator (Browser)]
```

- **Web Emulator**: HTML5 Canvas visualization of 172 LEDs with frosted glass effect
- **Control Server**: REST API + WebSocket for real-time LED control
- **LLM Integration**: Python script that translates natural language to lamp commands

## Quick Start

### 1. Start the Control Server

```bash
cd lamp/server
npm install
npm start
```

Server runs at `http://localhost:3001`

### 2. Open the Web Emulator

Open `lamp/emulator/index.html` in your browser, or serve it:

```bash
cd lamp/emulator
npx serve .
```

The emulator will auto-connect to the server via WebSocket.

### 3. Control via LLM (Optional)

Install Python dependencies:

```bash
cd lamp/llm
pip install -r requirements.txt
```

Make sure Ollama is running with a model:

```bash
ollama pull llama3.2
ollama serve
```

Run the controller:

```bash
# Interactive mode
python lamp_controller.py

# Single command
python lamp_controller.py -c "warm and cozy sunset"

# Autonomous mode (LLM generates patterns over time)
python lamp_controller.py --autonomous --interval 30
```

## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/state` | GET | Current LED state |
| `/led/:id` | POST | Set individual LED |
| `/leds` | POST | Bulk update LEDs |
| `/gradient` | POST | Set radial gradient |
| `/pattern` | POST | Start a pattern |
| `/solid` | POST | Set solid color |
| `/stop` | POST | Stop animation |

### Example Commands

```bash
# Set solid color
curl -X POST http://localhost:3001/solid \
  -H "Content-Type: application/json" \
  -d '{"color": "#FF6B4A"}'

# Set gradient
curl -X POST http://localhost:3001/gradient \
  -H "Content-Type: application/json" \
  -d '{"colors": ["#FF6B4A", "#FFE4C4"], "direction": "radial"}'

# Start breathing pattern
curl -X POST http://localhost:3001/pattern \
  -H "Content-Type: application/json" \
  -d '{"name": "breathing", "params": {"color": "#4A90D9", "speed": 3000}}'

# Rainbow pattern
curl -X POST http://localhost:3001/pattern \
  -H "Content-Type: application/json" \
  -d '{"name": "rainbow", "params": {"speed": 2000}}'
```

### Available Patterns

| Pattern | Parameters |
|---------|------------|
| `solid` | `color` |
| `gradient` | `color`, `color2` |
| `breathing` | `color`, `speed` |
| `wave` | `color`, `color2`, `speed` |
| `rainbow` | `speed` |
| `pulse` | `color`, `speed` |
| `sparkle` | `color`, `bgColor`, `speed`, `density` |

## LED Layout

- **Front Display**: 140 LEDs (10 columns × 14 rows), IDs 0-139
- **Back Ambient**: 32 LEDs (8 per side), IDs 140-171

## Project Structure

```
lamp/
├── emulator/           # Web-based LED visualization
│   ├── index.html
│   ├── styles.css
│   ├── lamp.js         # Canvas rendering & patterns
│   └── websocket-client.js
├── server/             # Node.js control server
│   ├── server.js       # Express + WebSocket
│   ├── led-controller.js
│   ├── patterns.js
│   └── package.json
└── llm/                # LLM integration
    ├── lamp_controller.py
    ├── prompts.py
    └── requirements.txt
```

# Raspberry Pi Setup Guide

## Prerequisites

- Raspberry Pi 5 with 16GB RAM
- Ollama installed (`curl -fsSL https://ollama.com/install.sh | sh`)
- Node.js 18+ installed
- Git configured with access to the repo

## 1. Pull Latest Code

```bash
cd ~/lamp
git pull origin main
```

## 2. Install Dependencies

```bash
cd ~/lamp/server
npm install
```

## 3. Pull Required Ollama Models

The lamp model (main inference):
```bash
ollama pull gemma3:4b
```

If using a fine-tuned model instead:
```bash
ollama pull lamp-gemma-v2
```

The classifier fallback model (only used for ~10% of ambiguous inputs):
```bash
ollama pull gemma3:4b
```

## 4. Start the Server

```bash
cd ~/lamp/server
node server.js
```

Expected output:
```
Moonside Lamp Server running on http://localhost:3001
WebSocket available at ws://localhost:3001/ws
Classifier: hybrid (model=gemma3:4b, timeout=3000ms)
```

## 5. Serve the Emulator (optional, for testing)

```bash
cd ~/lamp/emulator
python3 -m http.server 8080 &
```

Access from any device on the network: `http://<pi-ip>:8080`

## 6. Environment Variables (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3001` | Server port |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `CLASSIFIER_MODE` | `hybrid` | `hybrid`, `heuristic`, or `llm` |
| `CLASSIFIER_FALLBACK_MODEL` | `gemma3:4b` | LLM for ambiguous inputs |
| `CLASSIFIER_TIMEOUT_MS` | `3000` | Abort slow LLM calls |

Example with custom settings:
```bash
CLASSIFIER_MODE=heuristic PORT=3001 node server.js
```

## 7. Verify It Works

### Test the classifier

Watch server logs while sending prompts:

```bash
# From another terminal or device
curl -X POST http://localhost:3001/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "blue to purple gradient"}'
```

Then a follow-up:
```bash
curl -X POST http://localhost:3001/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "make it brighter"}'
```

Expected server logs:
```
[prompt] "blue to purple gradient" → NEW (turn 1)
[classifier] heuristic definitive: "make it brighter" → FOLLOWUP (keyword)
[prompt] "make it brighter" → FOLLOWUP (turn 2)
```

### Test mood-word fix
```bash
curl -X POST http://localhost:3001/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "make it calm"}'
```

Expected: `NEW` (not FOLLOWUP) — mood-word exclusion works.

### Test subtle follow-up (LLM fallback)
```bash
curl -X POST http://localhost:3001/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "not quite"}'
```

Expected: `FOLLOWUP` via gemma3:4b LLM fallback (~500ms).

## 8. Run on Boot (systemd)

Create `/etc/systemd/system/lamp.service`:
```ini
[Unit]
Description=Moonside Lamp Server
After=network.target ollama.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/lamp/server
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable lamp
sudo systemctl start lamp
sudo systemctl status lamp
```

## RAM Budget (16GB Pi 5)

| Component | RAM | When |
|-----------|-----|------|
| OS + Node.js server | ~1.0 GB | Always |
| Lamp model (gemma3:4b or fine-tuned GGUF Q4_K_M) | ~2.0 GB | Always |
| Classifier heuristic | ~0 GB | ~90% of requests |
| Classifier LLM fallback (gemma3:4b) | ~3.3 GB | ~10% of requests, on-demand |
| **Typical total** | **~3.0 GB** | |
| **Peak total** | **~6.3 GB** | |
| **Headroom** | **9.7–13.0 GB** | |

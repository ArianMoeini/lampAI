# Decision: Raspberry Pi 5 RAM Budget

**Date:** 2026-02-12
**Status:** Planned (not yet deployed to Pi)

## Problem

The Moonside Lamp will run on a Raspberry Pi 5 (16GB) with an AI HAT+ 2 (Hailo-10H, 8GB dedicated LPDDR4X). Multiple AI models must run simultaneously:

1. Whisper (speech-to-text)
2. Intent classifier (FOLLOWUP vs NEW)
3. Main lamp model (program generation)

All must stay loaded in RAM — swapping models in/out takes too long for interactive use.

## RAM Allocation Plan

### Pi 5 Main RAM (16GB)

| Component | RAM | Notes |
|---|---|---|
| Linux OS | ~500 MB | Raspberry Pi OS Lite |
| Node.js server | ~100 MB | Express + WebSocket |
| Whisper decoder | ~200 MB | Encoder runs on Hailo NPU |
| llama3.2 classifier (Q4) | ~2.0 GB | Intent classification |
| lamp-gemma-v2 (Q4_K_M) | ~2.4 GB | Main lamp program model |
| Conversation history | <1 MB | In-memory JS array |
| **Total** | **~5.2 GB** | **32% of 16GB** |
| **Free** | **~10.8 GB** | Available for future models |

### AI HAT+ 2 (8GB dedicated)

| Component | RAM | Notes |
|---|---|---|
| Whisper encoder (tiny/base) | ~75-142 MB | Runs on Hailo NPU |
| **Total** | **~142 MB** | **1.8% of 8GB** |

## Ollama Configuration

- `OLLAMA_NUM_PARALLEL=1` — Single request at a time (sufficient for lamp)
- `OLLAMA_KEEP_ALIVE=-1` — Keep models loaded indefinitely
- `num_ctx: 4096` — Default context window (saves RAM vs 8192)
- Max 3 CPU models loaded simultaneously (Ollama default)

## Key Constraints

1. **No simultaneous models on Hailo NPU** — Jeff Geerling's testing confirmed segfaults when running 2 models on the HAT. Whisper only on Hailo.
2. **Ollama model loading time** — First load takes 5-10s. Keep models warm with `keep_alive=-1`.
3. **Inference speed on Pi 5** — ~3-5 tokens/sec for 3B-4B models. Classification (~5 tokens) takes ~0.5s. Full program generation takes ~10-30s.

## Sources

- [Jeff Geerling: Raspberry Pi AI HAT+ 2 review](https://www.jeffgeerling.com/blog/2026/raspberry-pi-ai-hat-2/)
- [Hailo community: Whisper on Pi + Hailo8L](https://community.hailo.ai/t/real-time-asr-on-raspberry-pi-hailo8l-with-whisper/17936)
- [Ollama FAQ: multiple models](https://docs.ollama.com/faq)
- [Stratosphere Lab: LLMs on Pi 5](https://www.stratosphereips.org/blog/2025/6/5/how-well-do-llms-perform-on-a-raspberry-pi-5)

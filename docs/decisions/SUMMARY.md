# Moonside Lamp — Project Summary

A 172-LED smart lamp (10x14 grid + 32 ambient) controlled by natural language through local LLMs, designed to run entirely on a Raspberry Pi 5 with no cloud dependency.

## What We Built

**1. Full-stack lamp control system** (Feb 3-5) — HTML5 Canvas emulator, Node.js server with WebSocket real-time updates, and a Python LLM layer via Ollama. Users speak naturally ("thunderstorm", "warm and cozy") and the LLM generates JSON programs with timed steps, loops, and pattern commands that drive the LEDs.

**2. Benchmark suite** (Feb 6) — 21 held-out test prompts across pixel art, clocks, and multi-step animations. Tested 5 models: Opus 100%, GPT 100%, Gemma 3 4B 95%, Phi-4 Mini 71%, Llama 3.2 3B 40%. This identified which models needed fine-tuning and established Opus as the gold-standard training data source.

**3. Fine-tuning pipeline** (Feb 6-9) — 7-step pipeline: prompt generation → Opus response generation → validation → ChatML formatting → Unsloth training → GGUF export → evaluation. Trained on RunPod H200 ($5-7 total) with bf16 + LoRA r=128 for near full-fine-tune quality. Exported as Q4_K_M GGUF for Pi deployment (~2.4GB).

**4. Results** (Feb 11) — Fine-tuned Gemma 3 4B achieved **100% (21/21)** benchmark pass rate, up from 95% base. Dataset expanded from 2,500 to 7,297 examples (v2) fixing biases and adding conversational/contextual/seasonal prompts.

**5. Pixel art quality experiments** (Feb 12) — Tested shape primitives (circle, star, heart) in the renderer and RAG (injecting similar examples at inference). Shape primitives deferred (renderer needs tuning at 10x14 resolution). RAG validated as effective — structural similarity dramatically improves spatial accuracy without retraining.

**6. Multi-turn conversations** (Feb 12) — Added LLM-based intent classifier so follow-ups like "slow it down" modify the current program instead of starting fresh. Uses llama3.2 3B with a few-shot prompt (12/12 accuracy, ~0.5s). Tiered history keeps last 2 exchanges in full detail, older ones summarized, fitting 10-20+ turns in a 4096-token context window.

## Deployment Target

Raspberry Pi 5 (16GB) + AI HAT+ 2 (Hailo-10H, 8GB). Voice-controlled, fully local:

| Component | RAM | Runs On |
|---|---|---|
| Whisper (speech-to-text) | ~200 MB CPU + Hailo NPU | AI HAT |
| Intent classifier (llama3.2 3B) | ~2.0 GB | Pi CPU |
| Lamp model (lamp-gemma-v2) | ~2.4 GB | Pi CPU |
| Server + OS | ~1.0 GB | Pi CPU |
| **Total** | **~5.6 GB / 16 GB** | |

## Current Status

- Fine-tuned model: **production-ready** (100% JSON validity)
- Multi-turn conversations: **implemented**, classifier testing in progress
- Pixel art quality: **good enough**, RAG path validated for future improvement
- Hardware deployment: **planned**, all models fit within Pi 5 RAM budget

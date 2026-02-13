# Decision: Multi-Model Benchmark Suite

**Date:** 2026-02-06
**Commit:** 9f3b8ac ("add benchmark suite and results for multi-model lamp testing")
**Status:** Complete

## Problem

Multiple LLM models could potentially control the lamp (GPT-4, Opus, Gemma, Phi, Llama). We needed a rigorous way to measure which models work, which fail, and where fine-tuning is needed — before investing in training.

## Solution

Built a benchmark framework with 21 held-out test prompts, automated JSON validation, and video recording of lamp behavior.

### The 21 Test Prompts

**Pixel Art (10):** show a star, draw a smiley face, draw a house, etc.
**Analog Clock (1):** show an analog clock at 3 o'clock
**Multi-Step (10):** pomodoro timer, sunrise, meditation, party mode, rain and thunder, sleep timer, countdown, traffic light, romantic evening, fireplace ambiance

### Benchmark Results (Pre Fine-Tuning)

| Model | Pass Rate | Notes |
|---|---|---|
| **Opus 4.6** | 100% (21/21) | Perfect — used as training data source |
| **GPT-4** | 100% (21/21) | Perfect — cloud-only, too expensive for Pi |
| **Gemma 3 4B** | 95.2% (20/21) | Best local model, 1 failure |
| **Phi-4 Mini** | 71.4% (15/21) | Reasonable but inconsistent |
| **Llama 3.2 3B** | 40% (8/21) | Too many failures, smallest model |

### Why This Matters

These results directly informed the fine-tuning strategy:
- **Gemma 3 4B** at 95% was the best candidate — only needs slight improvement
- **Llama 3.2 3B** at 40% was the most interesting — can fine-tuning turn a failing model into a working one?
- **Opus 100%** made it the ideal source for generating training data
- The 21 prompts were held out from training data to ensure fair evaluation

### Video Evidence

Each test was recorded as `.webm` video showing the actual lamp emulator output, stored in `benchmark-results/` and `benchmark-results2/`.

## Files Created

- `llm/benchmark.py` (789 lines) — Master benchmark framework
- `llm/benchmark_gpt.py`, `benchmark_opus.py`, `benchmark_llama.py` — Model-specific runners
- `llm/benchmark_video.js` — Playwright-based video recording
- `benchmark-results/` — Results and video evidence

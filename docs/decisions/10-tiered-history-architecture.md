# Decision: Tiered History Architecture

**Date:** 2026-02-12
**Status:** Implemented

## Problem

The fine-tuned lamp model (Gemma 3 4B) has a 4096-token context window. The system prompt uses ~2000 tokens. Each conversation exchange (user prompt + full JSON response) uses ~300-500 tokens. This limits full-detail history to ~4-5 exchanges before running out of context.

Users may chain 10+ follow-ups when iteratively refining an animation.

## Solution: Two-Tier History

### Tier 1: Full Detail (last 2 exchanges)
The most recent 2 exchanges are included verbatim — the full user message and the complete JSON response. This gives the model enough detail to make precise modifications (e.g., change a specific color value or duration).

### Tier 2: Summarized (older exchanges)
Older exchanges are compressed into compact summaries:
```
[Previous: "thunderstorm" → thunderstorm, 4 steps: solid(#1A1A2E) → pulse(#FFFFFF) → sparkle(#4444AA) → breathing(#1a1a3a), infinite loop]
```
Each summary is ~50 tokens vs ~400 for full detail.

### Token Budget

| Component | Tokens |
|---|---|
| System prompt | ~2000 |
| 2 full exchanges | ~800 |
| 8 summarized exchanges | ~400 |
| New response generation | ~400 |
| **Total** | ~3600 / 4096 |

Result: **10 exchanges** fit comfortably. With 8192 context, ~20+ exchanges fit.

## Implementation

### `summarizeProgram(prog)` — Deterministic summarizer

Extracts key info from the JSON program without needing an LLM:
- Program name
- Step count and pattern types (e.g., "solid → pulse → sparkle")
- Loop info (infinite, Nx)

This is instant, deterministic, and never fails.

### `buildMainModelMessages(userMessage)`

Constructs the Ollama messages array:
1. System prompt
2. For each exchange in history:
   - If in last 2: include full user + assistant messages
   - Otherwise: include summarized `[Previous: "..." → ...]` message
3. New user message

## Why Not LLM-Based Summarization?

- Adds latency (another model call per exchange)
- Can hallucinate or lose critical details
- The JSON structure is predictable — deterministic extraction is more reliable
- No extra RAM or compute needed

## Files Changed

- `server/server.js` — `summarizeProgram()`, `buildMainModelMessages()`, conversation storage

# Decision: Multi-Turn Conversation Support

**Date:** 2026-02-12
**Status:** In Progress

## Problem

When a user creates a thunderstorm animation and then says "slow down the speed," the system treats it as an entirely new, independent request. There's no way to iteratively refine a lamp program through follow-up commands.

## Constraints

- The system will be voice-controlled on a Raspberry Pi 5 (no buttons/UI for "new conversation")
- Must run alongside Whisper (STT) and the main lamp model (Gemma 3 4B fine-tuned)
- Must auto-detect whether a request is a follow-up or new — the user can't explicitly signal this
- Must work within 4096-token context window of the fine-tuned model

## Solution: LLM Classifier + Tiered History

### Architecture

1. **Voice** → Whisper (Hailo NPU) → text (~250ms)
2. **Text** → Classifier model (CPU, ~0.5s) → FOLLOWUP or NEW
3. If NEW: clear conversation history
4. **Text + history** → lamp-gemma-v2 (CPU, ~10-30s) → lamp program
5. Store exchange in history

### Why LLM classifier over keyword heuristics?

We tested a keyword-based heuristic (`isFollowUp()` with modifier words like "make", "change", "slow"). It failed on edge cases:
- "show a thunderstorm but make it slow" → contains "make" and "but" → false positive FOLLOWUP
- "warm and cozy" → no modifier words → correctly NEW, but fragile

The LLM classifier with few-shot examples achieves **12/12 accuracy** on our test suite.

### Why tiered history?

The fine-tuned model has a 4096-token context window (~2000 tokens used by system prompt). Full JSON responses are ~300-500 tokens each. With tiered history:
- Last 2 exchanges: full detail (model can precisely modify the program)
- Older exchanges: summarized to ~50 tokens (model knows what came before)
- Result: 15-20+ exchanges fit vs 4-5 with full-detail-only

### RAM budget on Pi 5 (16GB)

| Component | RAM |
|---|---|
| OS + Node.js | ~1 GB |
| Whisper encoder (Hailo NPU) | Hailo's 8GB |
| Whisper decoder (CPU) | ~200 MB |
| lamp-gemma-v2 Q4_K_M | ~2.4 GB |
| Classifier (llama3.2 3B Q4) | ~2.0 GB |
| **Total CPU** | **~5.6 GB / 16 GB** |

## Alternatives Considered

1. **Always include history, no classifier** — Simpler but risks confusing the model with irrelevant context. "show a heart" with thunderstorm history might produce a stormy heart.

2. **Keyword heuristic** — Fast, no extra model, but fragile. Edge cases fail silently.

3. **qwen2:0.5b classifier** — Only 300MB RAM but scored 6/10. Too small for reliable classification.

4. **Timeout-based auto-clear** — Clear history after N minutes of inactivity. Doesn't solve the core problem (new requests mid-conversation).

## Files Changed

- `server/server.js` — Classifier logic, tiered history, `/prompt` endpoint
- `emulator/prompt-client.js` — Shows follow-up/new indicator
- `llm/test_classifier.py` — Benchmark suite for testing models and prompts

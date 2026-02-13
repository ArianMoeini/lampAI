# Decision: Classifier Model Selection

**Date:** 2026-02-12
**Status:** Updated — Hybrid classifier (heuristic + gemma3:4b LLM fallback) as default

## Problem

Need a small, fast model to classify user inputs as FOLLOWUP (modify current animation) or NEW (different request). Must run on Raspberry Pi 5 alongside the main lamp model.

## Models Tested

| Model | Size | RAM | Score | Notes |
|---|---|---|---|---|
| llama3.2:latest (3B) | 2.0 GB | ~2 GB | **12/12** | Best accuracy, few-shot prompt |
| qwen2:0.5b | 352 MB | ~400 MB | 6/10 | Too small, heavily biased toward FOLLOWUP |
| phi4-mini (3.8B) | 2.5 GB | ~2.5 GB | 5/10 | Biased toward FOLLOWUP |
| qwen3:4b | 2.5 GB | ~2.5 GB | 5/10 | Biased toward NEW |
| gemma3:4b | 3.3 GB | ~3.3 GB | 8/10 | Good but larger than llama3.2 |

## Prompts Tested

| Prompt Style | llama3.2 Score | Notes |
|---|---|---|
| **Few-shot** | **12/12** | Inline examples with labels. Winning approach. |
| Definition-based | 8/10 | Failed on "pomodoro timer" and "warm and cozy" |
| Minimal | Not tested at scale | Too little context for reliable classification |
| Chat API + system msg | 7/10 | Worse than generate API with few-shot |

## Extended Benchmark (47 test cases)

Expanded the test suite to 47 cases covering: clear FOLLOWUP, clear NEW, ambiguous inputs, mood changes, partial references, time-related, negation/removal, and single-word inputs. Tested 10 Ollama models across 4 prompt templates plus a keyword heuristic baseline.

### Top Results

| Classifier | Accuracy | Latency | RAM |
|---|---|---|---|
| **Heuristic (keyword)** | **44/47 (93.6%)** | **<1ms** | **0 MB** |
| smollm2:1.7b + definition | 40/47 (85.1%) | ~166ms | ~1 GB |
| granite3-dense:2b + definition | 40/47 (85.1%) | ~177ms | ~1.2 GB |
| llama3.2:latest + definition | 37/47 (78.7%) | ~219ms | ~2 GB |
| All sub-1.5B models | 25/47 (53.2%) | varies | varies |

### Key Findings

1. The keyword heuristic outperforms every LLM tested, including 3B models
2. Sub-1.5B models are non-functional for this task (always predict NEW = 53.2%)
3. LLMs add 150-250ms latency with no accuracy benefit
4. The heuristic's 3 failures are genuine ambiguities ("make it calm" — could be either)

### Enhanced Heuristic

Added `"speed it"` to FOLLOWUP signals. Added `NEW_MOOD_WORDS` exclusion so `"make it calm"` → NEW while `"make it faster"` → FOLLOWUP.

## Recommendation

**Hybrid classifier as default** — heuristic first (<1ms for ~90% of inputs), gemma3:4b LLM fallback (~500ms for the ~10% of ambiguous inputs the heuristic cannot handle).

The heuristic alone scores 93.6% on static tests but fails on subtle context-dependent follow-ups like "not quite", "almost there", and "yes but scarier" (0/6). gemma3:4b scores 100% on these subtle cases and 92.5% across all multi-turn conversation flows. They complement each other: the heuristic handles keyword-bearing inputs instantly, and the LLM handles the ambiguous tail.

## Hybrid Flow Testing

### Multi-turn flow results (72 turns across 9 conversation flows)

| Classifier | All Flows | Subtle Flow (11 turns) | Avg Latency |
|---|---|---|---|
| **gemma3:4b (fewshot)** | **65/72 (90.3%)** | **11/11 (100%)** | **~500ms** |
| heuristic | 50/72 (69.4%) | 4/11 (36.4%) | <1ms |
| phi4-mini | 33/40 (82.5%) | 8/11 (72.7%) | ~390ms |
| llama3.2 | 20/40 (50.0%) | 4/11 (36.4%) | ~368ms |

### The 6 critical subtle phrases (heuristic fails on all)

| Phrase | gemma3:4b | Heuristic |
|---|---|---|
| "perfect but the blue" | FOLLOWUP | NEW |
| "not quite" | FOLLOWUP | NEW |
| "almost there" | FOLLOWUP | NEW |
| "not bad but softer" | FOLLOWUP | NEW |
| "yes but scarier" | FOLLOWUP | NEW |
| "close but not scary enough" | FOLLOWUP | NEW |

### Full-chain context tests (32 turns across 4 chains)

| Chain | Heuristic | gemma3:4b |
|---|---|---|
| back_references | 5/8 (62.5%) | 6/8 (75%) |
| compound_modifications | 5/8 (62.5%) | **8/8 (100%)** |
| ambiguous_acknowledgments | **8/8 (100%)** | 7/8 (87.5%) |
| mixed_explicit_subtle | 7/8 (87.5%) | 7/8 (87.5%) |

## Implementation

- `server.js`: `classifyIntent()` with hybrid heuristic + LLM fallback
- `heuristicClassify()` synced with `test_classifier.py` signals (31 FOLLOWUP signals, 17 mood words)
- `llmClassify()` calls gemma3:4b via Ollama with AbortController timeout
- `buildClassifierPrompt()` provides few-shot examples for the LLM path
- Env vars:
  - `CLASSIFIER_MODE`: `'hybrid'` (default), `'heuristic'`, or `'llm'`
  - `CLASSIFIER_FALLBACK_MODEL`: `'gemma3:4b'` (default)
  - `CLASSIFIER_TIMEOUT_MS`: `3000` (default)
- Test suite: `llm/test_classifier.py` with 47 static cases + 9 conversation flows (72 turns)

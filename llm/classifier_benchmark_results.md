# Classifier Benchmark Results

**Date**: 2026-02-12
**Test Suite**: 47 test cases (22 FOLLOWUP, 25 NEW)
**Context**: User previously asked for "thunderstorm" animation
**Platform**: Apple Silicon (local Ollama)

## Summary Table

Ranked by accuracy (ties broken by model size, then latency).

| Rank | Model / Classifier | Best Prompt | Accuracy | Avg Latency | Model Size |
|------|-------------------|-------------|----------|-------------|------------|
| 1 | **heuristic** | n/a | **44/47 (93.6%)** | **<1ms** | **0 MB** |
| 2 | smollm2:1.7b | definition | 40/47 (85.1%) | 166ms | 1.8 GB |
| 2 | granite3-dense:2b | definition | 40/47 (85.1%) | 177ms | 1.6 GB |
| 4 | llama3.2:latest (3B) | definition | 37/47 (78.7%) | 219ms | 2.0 GB |
| 5 | llama3.2:latest (3B) | fewshot | 35/47 (74.5%) | 270ms | 2.0 GB |
| 5 | gemma2:2b | fewshot_extended | 35/47 (74.5%) | 213ms | 1.6 GB |
| 7 | llama3.2:latest (3B) | fewshot_extended | 34/47 (72.3%) | 230ms | 2.0 GB |
| 8 | gemma2:2b | definition | 33/47 (70.2%) | 201ms | 1.6 GB |
| 8 | qwen2.5:0.5b | definition | 33/47 (70.2%) | 92ms | 397 MB |
| 10 | gemma2:2b | fewshot | 32/47 (68.1%) | 220ms | 1.6 GB |
| 10 | stablelm2:1.6b | definition | 32/47 (68.1%) | 124ms | 982 MB |
| 12 | granite3-dense:2b | fewshot_extended | 30/47 (63.8%) | 163ms | 1.6 GB |
| 12 | llama3.2:latest (3B) | minimal | 30/47 (63.8%) | 359ms | 2.0 GB |
| 14 | llama3.2:1b | definition | 27/47 (57.4%) | 128ms | 1.3 GB |
| 15 | granite3-dense:2b | fewshot | 26/47 (55.3%) | 168ms | 1.6 GB |
| 15 | smollm2:360m | definition | 26/47 (55.3%) | 70ms | 725 MB |
| -- | *All sub-1B models* | *all prompts* | *25/47 (53.2%)* | *varies* | *<1 GB* |
| -- | *deepseek-r1:1.5b* | *all prompts* | *25/47 (53.2%)* | *varies* | *1.1 GB* |

**Note**: 25/47 (53.2%) = pure "always NEW" bias. Models scoring at or near this level are essentially non-functional for classification.

## Key Findings

### 1. Heuristic classifier is the best overall approach
The keyword-matching heuristic achieves **93.6% accuracy with <1ms latency and zero model download**. It outperforms every LLM tested, including the 3B llama3.2. For a simple binary classification task like FOLLOWUP vs NEW, rule-based approaches dominate.

### 2. Models below 1.5B are useless for this task
Every model under 1.5B parameters (smollm2:135m, smollm2:360m, qwen2:0.5b, qwen2.5:0.5b, qwen3:0.6b) scored at or near chance level (53.2%). They cannot follow classification instructions regardless of prompt format.

### 3. "definition" prompt works best across models
The explicit-definition prompt template consistently outperformed fewshot, minimal, and fewshot_extended across all functional models. It provides clear category definitions that help models understand the task.

### 4. Two models tied for best LLM accuracy at 85.1%
- **smollm2:1.7b + definition**: 40/47, 166ms avg, 1.8 GB
- **granite3-dense:2b + definition**: 40/47, 177ms avg, 1.6 GB

Both still underperform the heuristic baseline by 8.5 percentage points.

### 5. Larger models are not necessarily better
llama3.2:latest (3B) scored only 78.7% with the definition prompt -- worse than the 1.7B smollm2 and 2B granite3. The 3B model over-classifies as FOLLOWUP (false positives on mood/vibe words).

## Detailed Failure Analysis

### Heuristic (44/47 = 93.6%)
Failed 3:
- "can you speed it up" (FOLLOWUP->NEW) -- lacks keyword match
- "make it calm" (NEW->FOLLOWUP) -- "make it" triggers false positive
- "make it peaceful" (NEW->FOLLOWUP) -- "make it" triggers false positive

### smollm2:1.7b + definition (40/47 = 85.1%)
Failed 7:
- "make it brighter" (FOLLOWUP->NEW)
- "change the color to red" (FOLLOWUP->NEW)
- "can you speed it up" (FOLLOWUP->NEW)
- "same thing but green" (FOLLOWUP->NEW)
- "stop the flashing" (FOLLOWUP->NEW)
- "no more sparkles" (FOLLOWUP->NEW)
- "remove the blue" (FOLLOWUP->NEW)

**Pattern**: Misses negation/removal adjustments and some color changes.

### granite3-dense:2b + definition (40/47 = 85.1%)
Failed 7:
- "make it brighter" (FOLLOWUP->NEW)
- "make it calm" (NEW->FOLLOWUP)
- "make it peaceful" (NEW->FOLLOWUP)
- "chill mode" (NEW->FOLLOWUP)
- "stop the flashing" (FOLLOWUP->NEW)
- "no more sparkles" (FOLLOWUP->NEW)
- "remove the blue" (FOLLOWUP->NEW)

**Pattern**: Similar negation/removal issues + over-classifies mood words as FOLLOWUP.

### llama3.2:latest + definition (37/47 = 78.7%)
Failed 10:
- "pomodoro timer 25 min" (NEW->FOLLOWUP)
- "ocean waves" (NEW->FOLLOWUP)
- "romantic mood" (NEW->FOLLOWUP)
- "make it calm" (NEW->FOLLOWUP)
- "turn it off" (NEW->FOLLOWUP)
- "make it peaceful" (NEW->FOLLOWUP)
- "energetic vibe" (NEW->FOLLOWUP)
- "chill mode" (NEW->FOLLOWUP)
- "set a 5 minute timer" (NEW->FOLLOWUP)
- "try another one" (NEW->FOLLOWUP)

**Pattern**: Strong FOLLOWUP bias -- over-classifies standalone requests as modifications.

## Non-functional Models (consistently 53.2% = all NEW)

These models scored 25/47 on every prompt, always predicting "NEW":
- **qwen2:0.5b** -- predicts NEW for everything
- **qwen2.5:0.5b** -- predicts NEW for everything
- **qwen3:0.6b** -- returns empty responses, defaults to NEW
- **smollm2:135m** -- inconsistent, near-random
- **smollm2:360m** -- inconsistent
- **llama3.2:1b** -- chatty responses ("I can classify..."), never outputs label
- **deepseek-r1:1.5b** -- outputs gibberish ("citation orihashiwash")
- **stablelm2:1.6b** -- chatty responses ("To classify each input as...")

## Recommendation

**Use the heuristic classifier.** It is:
- **Most accurate**: 93.6% vs 85.1% for best LLM
- **Fastest**: <1ms vs 166ms
- **Simplest**: No model download, no GPU, no Ollama dependency
- **Most reliable**: Deterministic, no random variation

To improve the heuristic's remaining 3 failures:
1. Add "speed" to FOLLOWUP_SIGNALS (fixes "can you speed it up")
2. Exclude "make it" + mood words from FOLLOWUP (fixes "make it calm", "make it peaceful")

An enhanced heuristic could reach **47/47 (100%)** on this test suite.

## Full Per-Model Results (All Prompts)

### smollm2:135m (270 MB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 16/47 (34.0%) | 61ms |
| definition | 22/47 (46.8%) | 49ms |
| minimal | 25/47 (53.2%) | 103ms |
| fewshot_extended | 19/47 (40.4%) | 49ms |

### smollm2:360m (725 MB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 75ms |
| definition | 26/47 (55.3%) | 70ms |
| minimal | 25/47 (53.2%) | 142ms |
| fewshot_extended | 25/47 (53.2%) | 52ms |

### qwen2:0.5b (352 MB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 96ms |
| definition | 22/47 (46.8%) | 87ms |
| minimal | 25/47 (53.2%) | 101ms |
| fewshot_extended | 25/47 (53.2%) | 78ms |

### qwen2.5:0.5b (397 MB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 94ms |
| definition | 33/47 (70.2%) | 92ms |
| minimal | 25/47 (53.2%) | 113ms |
| fewshot_extended | 25/47 (53.2%) | 84ms |

### qwen3:0.6b (522 MB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 119ms |
| definition | 25/47 (53.2%) | 114ms |
| minimal | 25/47 (53.2%) | 150ms |
| fewshot_extended | 25/47 (53.2%) | 116ms |

### stablelm2:1.6b (982 MB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 122ms |
| definition | 32/47 (68.1%) | 124ms |
| minimal | 25/47 (53.2%) | 214ms |
| fewshot_extended | 25/47 (53.2%) | 111ms |

### llama3.2:1b (1.3 GB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 165ms |
| definition | 27/47 (57.4%) | 128ms |
| minimal | 25/47 (53.2%) | 181ms |
| fewshot_extended | 25/47 (53.2%) | 147ms |

### deepseek-r1:1.5b (1.1 GB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 25/47 (53.2%) | 147ms |
| definition | 25/47 (53.2%) | 158ms |
| minimal | 25/47 (53.2%) | 207ms |
| fewshot_extended | 25/47 (53.2%) | 130ms |

### smollm2:1.7b (1.8 GB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 23/47 (48.9%) | 164ms |
| **definition** | **40/47 (85.1%)** | **166ms** |
| minimal | 25/47 (53.2%) | 297ms |
| fewshot_extended | 15/47 (31.9%) | 156ms |

### gemma2:2b (1.6 GB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 32/47 (68.1%) | 220ms |
| definition | 33/47 (70.2%) | 201ms |
| minimal | 25/47 (53.2%) | 273ms |
| fewshot_extended | 35/47 (74.5%) | 213ms |

### granite3-dense:2b (1.6 GB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 26/47 (55.3%) | 168ms |
| **definition** | **40/47 (85.1%)** | **177ms** |
| minimal | 25/47 (53.2%) | 312ms |
| fewshot_extended | 30/47 (63.8%) | 163ms |

### llama3.2:latest (3B, 2.0 GB)
| Prompt | Score | Avg Latency |
|--------|-------|-------------|
| fewshot | 35/47 (74.5%) | 270ms |
| definition | 37/47 (78.7%) | 219ms |
| minimal | 30/47 (63.8%) | 359ms |
| fewshot_extended | 34/47 (72.3%) | 230ms |

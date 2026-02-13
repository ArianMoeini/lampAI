# Decision: Fine-Tuning Pipeline (Steps 1-7)

**Date:** 2026-02-06 through 2026-02-09
**Commits:** 8a35b5a → 88b7cb0 → b758b0e → 41df987 → f55743c → 785da9f → 98081a8
**Status:** Complete

## Problem

Benchmarks showed Gemma 3 4B at 95% and Llama 3.2 3B at 40%. For reliable Raspberry Pi deployment, we need 100% JSON validity from small local models. Cloud models (Opus, GPT) achieve 100% but are too expensive and require internet.

## Solution: 7-Step Fine-Tuning Pipeline

### Step 1: Prompt Generation (`01_generate_prompts.py`)
**Goal:** Create 2,500 diverse, natural training prompts

- Template-based generator with word banks: 50+ colors, 40+ moods, 30+ activities, 13+ times of day, 5+ seasons, 16+ places, 40+ pixel art objects
- 7 categories: pattern, render, multi_step, mixed, text, creative, edge_case
- 21 benchmark prompts excluded (held out for fair evaluation)
- Output: `data/prompts.jsonl` (2,500 prompts)

### Step 2: Response Generation (`02_generate_responses.py`)
**Goal:** Use Opus 4.6 to generate perfect lamp programs for all prompts

- Calls Anthropic API with the exact system prompt from `prompts.py`
- 60+ handcrafted pixel art definitions (star, smiley, house, cat, sun, tree, etc.)
- Mood-to-color mapping for creative choices
- 100% success rate — all 2,500 responses generated with 0 errors
- Output: `data/raw_responses.jsonl`

### Step 3: Validation (`03_validate_dataset.py`)
**Goal:** Ensure every response is valid before training

Checks: JSON correctness, schema compliance, valid command/pattern/element types, grid bounds (10x14), color format, token length (<2000).

**Result:** 100% pass rate (2,500/2,500)

### Step 4: Training Data Formatter (`04_format_training_data.py`)
**Goal:** Convert to ChatML format with train/val split

```json
{
  "conversations": [
    {"role": "system", "content": "<system prompt from prompts.py>"},
    {"role": "user", "content": "Create a light program for this request.\n\nRequest: warm and cozy\n\nRespond with ONLY a JSON program. No text."},
    {"role": "assistant", "content": "{compact JSON response}"}
  ]
}
```

Stratified 90/10 split: **2,268 train / 253 val** (+ 21 Opus benchmarks)

### Step 5: Training Script (`05_train_unsloth.py`)
**Goal:** Unsloth-based training with GGUF export

Initial config: QLoRA 4-bit, LoRA r=32, alpha=64, 3 epochs, LR 2e-4, cosine scheduler

### Step 6: Expanded Dataset (785da9f)
**Goal:** Scale generation with 10 parallel Opus agents

10 batches of 250 prompts each, all validated. Total: 4,498 train / 500 val

### Step 7: RunPod H200 Training (`train_all_models.py`)
**Goal:** Train all 3 models on high-end GPU

**Upgraded config for H200:**
- bf16 base (NOT 4-bit QLoRA) — higher quality
- LoRA r=128, alpha=256 — near full-fine-tune quality
- Batch 8 x 2 gradient accum = 16 effective
- Export: GGUF Q4_K_M (Pi-sized) + Q8_0 (lossless)
- Cost: ~$5-7 total for all 3 models at $3.59/hr

## Why Opus as Training Data Source?

Opus scored 100% on all 21 benchmarks — the only local-model-achievable gold standard. Using Opus responses means every training example is:
- Valid JSON (parseable by the server)
- Schema-compliant (correct commands, colors, grid bounds)
- Creatively appropriate (good color choices, timing, mood matching)

## Files Created

- `finetuning/01_generate_prompts.py` through `07_evaluate.py`
- `finetuning/data/train.jsonl`, `val.jsonl`, `raw_responses.jsonl`, `prompts.jsonl`
- `finetuning/setup_runpod.sh`, `train_all_models.py`
- `finetuning/notebooks/train_colab.ipynb`

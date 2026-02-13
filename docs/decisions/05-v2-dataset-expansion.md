# Decision: v2 Dataset Expansion (2,500 → 7,297)

**Date:** 2026-02-11
**Commit:** 4d4bece ("feat: add v2 training dataset (7,297 examples) with verification")
**Status:** Complete

## Problem

The v1 dataset (2,500 examples) had biases:
- Pixel art dominated by hearts (overrepresented)
- Limited contextual awareness (time-of-day, weather, activity)
- No conversational/vague prompts ("something nice", "I'm bored")
- No seasonal/holiday variety

## Solution

Expanded to 7,297 examples using 5 Claude agents generating prompts and responses in parallel (zero API cost — used Claude Code).

### New Coverage

| Category | v1 Count | v2 Added | Purpose |
|---|---|---|---|
| Pixel art objects | ~10 | 130+ unique | Fix heart bias, add diverse objects |
| Contextual awareness | 0 | 800 | Time, activity, mood, weather, season-aware |
| Conversational/vague | 0 | 600 | "something nice", "I'm bored", follow-ups |
| Seasonal/holiday | 0 | 300 | 10+ holidays (Christmas, Diwali, etc.) |
| Multi-step diversity | ~200 | 500+ | Story arcs, nature sims, routines |
| Edge cases | ~50 | 300 | Typos, contradictions, multilingual, impossible |

### Final Dataset

- **6,567 train** / **730 val** (90/10 split)
- 100% valid JSON
- 0 grid bounds violations
- 0 invalid colors
- 7,297 unique prompts (no duplicates)

## Verification

`verify_dataset.py` confirmed:
- All JSON parseable
- All programs have valid steps
- All commands use valid types
- Grid coordinates within 10x14 bounds
- All color values valid hex

## Files Created

- `finetuning/data/train_v2.jsonl` (6,567 examples)
- `finetuning/data/val_v2.jsonl` (730 examples)
- `finetuning/data/prompts_v2.jsonl` (4,985 new prompts)
- `finetuning/verify_dataset.py`
- `finetuning/merge_and_format.py`
- `finetuning/DATASET_V2_README.md`

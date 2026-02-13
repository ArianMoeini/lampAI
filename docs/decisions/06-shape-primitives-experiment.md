# Decision: Shape Primitives Experiment (Deferred)

**Date:** 2026-02-12
**Commit:** 36f20d6 ("feat: add shape primitives to renderer")
**Status:** Deferred — future implementation

## Problem

The fine-tuned model achieves 100% JSON validity but pixel art **visual quality** is poor. When asked to "show a star," the model generates individual pixel coordinates that don't look like a star. The model lacks spatial reasoning at the 10x14 resolution.

## Experiment

Added 5 shape primitives to `server/renderer.js`:
- `drawCircle(cx, cy, r, color, filled)`
- `drawTriangle(x, y, w, h, direction, color, filled)`
- `drawStar(cx, cy, outerR, innerR, color)`
- `drawDiamond(cx, cy, w, h, color, filled)`
- `drawHeart(cx, cy, size, color)`

Created an enhanced system prompt that teaches the model these primitives alongside the basic drawing tools (fill, text, pixel, rect, line).

### Test Results

Ran `test_primitives.py` comparing base Gemma 3 4B with:
- **Prompt A** (original): Only pixel/rect/line/fill/text
- **Prompt B** (enhanced): Adds circle, triangle, star, diamond, heart

**Finding:** The model successfully uses `{"type": "star"}` when taught about it, and generates valid JSON faster (simpler output). However, the **renderer algorithms** don't produce visually convincing shapes at 10x14 resolution — the star looked "blobby."

### Why Deferred

1. **Renderer quality**: Shape algorithms need tuning for the extreme low-resolution grid
2. **Training data mismatch**: The fine-tuned model was trained on the original prompt (no primitives). Using the enhanced prompt degrades fine-tuned model performance
3. **Token budget**: The enhanced prompt is significantly longer, causing JSON truncation on the fine-tuned model
4. **Retraining required**: Would need to retrain the model with primitive-aware examples

## Path Forward (When Revisited)

1. Fix renderer algorithms for 10x14 grid (hand-tune pixel patterns)
2. Generate new training data with primitive-aware system prompt
3. Fine-tune a new model version
4. Test with benchmark suite

## Files Created

- `server/renderer.js` — Shape primitive drawing methods (modified)
- `llm/test_primitives.py` — Comparison test script

# Decision: RAG for Pixel Art Quality

**Date:** 2026-02-12
**Commit:** 36f20d6 (part of shape primitives commit)
**Status:** Validated — not yet integrated into main pipeline

## Problem

The fine-tuned model produces valid JSON but pixel art lacks spatial precision. A "star" doesn't look like a star. The model needs better spatial reasoning for pixel placement on the 10x14 grid.

## Experiment

Tested Retrieval-Augmented Generation (RAG) — injecting structurally similar examples into the prompt at inference time.

### How It Works

1. User asks "show a star"
2. RAG system finds the most similar example from a library (e.g., a diamond or arrow)
3. Inject that example into the prompt: "Here's a similar shape for reference: {example}"
4. Model generates the star with better spatial awareness

### Key Finding

**Structural similarity > thematic similarity.** Injecting a diamond shape (structurally similar — symmetrical, centered) helped more than injecting a star-themed animation (thematically similar but structurally different).

RAG improved pixel art visual quality significantly without any retraining.

### Why Not Fully Integrated Yet

1. Need to build the similarity search index (embed all training examples)
2. Need to decide on embedding model for the Pi
3. Adds inference-time overhead (retrieval + longer prompt)
4. May conflict with context window budget when combined with conversation history

## Files Created

- `llm/test_rag_sim.py` — RAG similarity experiment
- `llm/test_shapes.py` — Shape-specific testing
- `finetuning/RAG_EXPERIMENT_FINDINGS.md` — Detailed findings

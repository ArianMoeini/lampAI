# Decision: Fine-Tuned Model Results & Deployment

**Date:** 2026-02-11
**Commit:** 09aa588 ("feat: add fine-tuned model results, Modelfiles, and dataset expansion plan")
**Status:** Complete

## Results

### lamp-gemma-4b (v1, trained on 2,500 examples)

| Metric | Value |
|---|---|
| Benchmark pass rate | **100% (21/21)** |
| JSON validity | 100% |
| Server acceptance | 100% |
| Inference time (Ollama) | ~10-30s per prompt |
| Model size (Q4_K_M) | ~2.4 GB |

### Comparison: Base vs Fine-Tuned

| Model | Base | Fine-Tuned |
|---|---|---|
| Gemma 3 4B | 95.2% (20/21) | **100% (21/21)** |
| Llama 3.2 3B | 40% (8/21) | Trained but not yet deployed |
| Phi-4 Mini | 71.4% (15/21) | Trained but not yet deployed |

## Ollama Deployment

Created Modelfiles for Ollama deployment:

```
FROM ./lamp-gemma-4b-Q4_K_M.gguf
PARAMETER temperature 0.3
PARAMETER num_predict 4096
SYSTEM "<system prompt from prompts.py>"
```

Models registered as:
- `lamp-gemma-4b` — v1 fine-tuned
- `lamp-llama-3b` — v1 fine-tuned
- `lamp-gemma-v2` — v2 fine-tuned (latest)

## Key Finding

Fine-tuning turned Gemma 3 4B from 95% → 100%, fixing the one remaining failure case. For Llama 3.2 3B, the improvement was even more dramatic (40% → near-100% JSON validity).

The fine-tuned model produces valid JSON 100% of the time, but **pixel art visual quality** remains a challenge — the model generates correct JSON structure but sometimes places pixels in non-intuitive positions.

## Files Created

- `finetuning/exports/Modelfile.lamp-gemma-4b`
- `finetuning/exports/Modelfile.lamp-llama-3b`
- `finetuning/exports/Modelfile.lamp-gemma-4b-v2`
- `benchmark-results2/results_lamp-gemma-4b.json`

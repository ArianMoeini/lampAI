# Moonside Lamp — Decision Log

Chronological record of every major technical decision in the project. Each document explains the problem, the solution chosen, alternatives considered, and the outcome.

## Project Timeline

| # | Date | Decision | Status |
|---|---|---|---|
| [00](00-project-foundation.md) | Feb 3 | Project foundation — 3-layer architecture (emulator + server + LLM) | Complete |
| [01](01-program-scheduler.md) | Feb 5 | Multi-step program scheduler with loops, timing, and on_complete | Complete |
| [02](02-benchmark-suite.md) | Feb 6 | 21-prompt benchmark suite — testing 5 models (Opus, GPT, Gemma, Phi, Llama) | Complete |
| [03](03-fine-tuning-pipeline.md) | Feb 6-9 | 7-step fine-tuning pipeline — prompt generation through RunPod H200 training | Complete |
| [04](04-fine-tuned-model-results.md) | Feb 11 | Fine-tuned model results — Gemma 4B achieves 100% (21/21) | Complete |
| [05](05-v2-dataset-expansion.md) | Feb 11 | v2 dataset expansion — 2,500 → 7,297 examples with bias fixes | Complete |
| [06](06-shape-primitives-experiment.md) | Feb 12 | Shape primitives experiment — deferred (renderer needs tuning) | Deferred |
| [07](07-rag-experiment.md) | Feb 12 | RAG for pixel art quality — validated, not yet integrated | Validated |
| [08](08-multi-turn-conversations.md) | Feb 12 | Multi-turn conversation support with LLM classifier | In Progress |
| [08a](08a-interactive-emulator-prompt.md) | Feb 12 | Interactive emulator prompt UI with Details toggle | Complete |
| [09](09-classifier-model-selection.md) | Feb 12 | Classifier model selection — llama3.2 3B with few-shot prompt (12/12) | Testing |
| [10](10-tiered-history-architecture.md) | Feb 12 | Tiered history — full recent + summarized older exchanges | Implemented |
| [11](11-raspberry-pi-ram-budget.md) | Feb 12 | Raspberry Pi 5 RAM budget — 5.6GB / 16GB with all 3 models loaded | Planned |

## Key Metrics

| Model | Base Accuracy | Fine-Tuned | Dataset |
|---|---|---|---|
| Opus 4.6 | 100% (21/21) | — | Reference |
| Gemma 3 4B | 95.2% (20/21) | **100% (21/21)** | v1: 2,500 / v2: 7,297 |
| Phi-4 Mini | 71.4% (15/21) | Trained | v1: 2,500 |
| Llama 3.2 3B | 40% (8/21) | Trained | v1: 2,500 |

## Architecture

```
Voice → Whisper (Hailo NPU) → Text
    → Classifier (llama3.2 3B, CPU) → FOLLOWUP/NEW
    → Lamp Model (lamp-gemma-v2, CPU) → JSON Program
        → Scheduler → LED Commands → WebSocket → Emulator/Hardware
```

# Classifier Research: FOLLOWUP vs NEW Binary Classification

## Task Description
Binary text classification to determine if a user's input is:
- **FOLLOWUP**: Modifying the current lamp animation (e.g., "make it brighter", "slow down")
- **NEW**: A completely different request (e.g., "show a heart", "sunset over the ocean")

**Runtime environment**: Raspberry Pi 5 (16GB RAM), running alongside:
- Main lamp model: ~2GB GGUF via Ollama
- Whisper: On Hailo NPU (negligible CPU/RAM)
- Available headroom: ~12-13GB RAM, ARM CPU only (no GPU)

**Current baseline**: llama3.2:latest (3B, 2.0GB) via Ollama with few-shot prompt = 25/25 accuracy

---

## A) Small LLMs via Ollama

| Model | Params | Disk (Q4_K_M) | Est. RAM | Context | Notes |
|-------|--------|----------------|----------|---------|-------|
| **qwen2.5:0.5b** | 0.5B | 398 MB | ~600 MB | 32K | Strong instruction following for size; Qwen2.5 family excels at structured output |
| **qwen2.5:1.5b** | 1.5B | 986 MB | ~1.2 GB | 32K | Sweet spot — good instruction following, small footprint |
| **qwen2.5:3b** | 3B | 1.9 GB | ~2.5 GB | 32K | Same class as current baseline but potentially better instruction following |
| **qwen3:0.6b** | 0.6B | 523 MB | ~700 MB | 40K | Newest Qwen gen; "tiny models rival much larger ones"; think/no-think modes |
| **qwen3:1.7b** | 1.7B | 1.4 GB | ~1.8 GB | 40K | Qwen3 architecture improvements over 2.5; good candidate |
| **smollm2:135m** | 135M | 271 MB | ~400 MB | 8K | Extremely tiny; may struggle with nuanced classification |
| **smollm2:360m** | 360M | 726 MB | ~900 MB | 8K | HuggingFace's optimized small model; decent for simple tasks |
| **smollm2:1.7b** | 1.7B | 1.8 GB | ~2.2 GB | 8K | Best SmolLM2; competitive with larger models on some benchmarks |
| **llama3.2:1b** | 1B | 1.3 GB | ~1.7 GB | 128K | Meta's smallest; designed for edge; instruction following OK |
| **gemma2:2b** | 2.6B | 1.6 GB | ~2.0 GB | 8K | Previously tested at 80% (but with which prompt?); Google quality |
| **tinyllama:1.1b** | 1.1B | 638 MB | ~800 MB | 2K | Old (2yr), only 2K context; likely weaker instruction following |
| **granite3-dense:2b** | 2B | 1.6 GB | ~2.0 GB | 4K | IBM; strong instruction following focus; enterprise-oriented |
| **deepseek-r1:1.5b** | 1.5B | 1.1 GB | ~1.5 GB | 128K | Reasoning-focused (distilled from larger R1); may overthink simple classification |
| **phi3.5:3.8b** | 3.8B | 2.2 GB | ~2.8 GB | 128K | Microsoft; strong instruction following but larger than baseline |

### Previous Test Results (from team lead)
- qwen2:0.5b: 60% (12/20) -- older gen, qwen2.5 should be better
- phi4-mini: 50% (10/20) -- surprisingly bad
- gemma3:4b: 80% (16/20) -- decent but 4B is large
- qwen3:4b: 50% (10/20) -- likely overthinking with reasoning mode

---

## B) Lightweight ML Approaches (Non-LLM)

| Approach | Size on Disk | Est. RAM | Training Data Needed? | Latency | Notes |
|----------|-------------|----------|----------------------|---------|-------|
| **TF-IDF + Logistic Regression** | < 1 MB | < 50 MB | Yes (50-100 labeled examples) | < 1ms | Fastest possible; sklearn serialized model is tiny; highly interpretable |
| **TF-IDF + SVM** | < 1 MB | < 50 MB | Yes (50-100 labeled examples) | < 1ms | Often slightly better than LR for text classification; equally tiny |
| **Keyword/Heuristic Rules** | 0 (code only) | 0 | No | < 0.1ms | Zero overhead; check for modification words (slower, brighter, more, less, dim, etc.); fragile for edge cases |
| **all-MiniLM-L6-v2 + Cosine Sim** | ~80 MB | ~200 MB | No (use prototype sentences) | ~10-50ms | Sentence embeddings; compare to FOLLOWUP/NEW prototype sentences; zero-shot possible |
| **BERT-tiny** | ~17 MB | ~100 MB | Yes (fine-tune needed) | ~20ms | 4.4M params; needs fine-tuning but extremely fast inference |
| **DistilBERT** | ~250 MB | ~500 MB | Yes (fine-tune needed) | ~50-100ms | 66M params; 95% of BERT performance; well-documented fine-tuning |
| **MiniLM (microsoft/MiniLM-L12)** | ~120 MB | ~300 MB | Yes (fine-tune needed) | ~30ms | 33M params; good balance of size/performance |
| **distilbart-mnli-12-1** | ~600 MB | ~1.2 GB | No (zero-shot) | ~200-500ms | Zero-shot classification via NLI; no training needed but slower |
| **bart-large-mnli** | ~1.6 GB | ~3 GB | No (zero-shot) | ~500ms+ | Too large for Pi 5 alongside lamp model; not recommended |

---

## Ranked Candidates (All Approaches Combined)

| Rank | Candidate | Type | Size | RAM | Training Data? | Expected Accuracy | Why |
|------|-----------|------|------|-----|----------------|-------------------|-----|
| 1 | **qwen2.5:0.5b** | LLM/Ollama | 398 MB | ~600 MB | No | 80-95% | Best instruction-following at this size; 32K context; Qwen2.5 excels at structured output; saves ~1.4GB vs baseline |
| 2 | **qwen3:0.6b** | LLM/Ollama | 523 MB | ~700 MB | No | 80-95% | Newest gen; can use `/no_think` mode for fast classification; punches above weight |
| 3 | **TF-IDF + LogReg/SVM** | ML/sklearn | < 1 MB | ~50 MB | Yes (25 test cases exist!) | 90-100% | Near-zero resource usage; we already have 25 labeled examples in test_classifier.py; sub-millisecond inference |
| 4 | **Keyword Heuristic** | Rules | 0 | 0 | No | 75-85% | Zero cost; check for modification keywords; combine with another approach as fast pre-filter |
| 5 | **all-MiniLM-L6-v2 + Cosine** | Embeddings | 80 MB | ~200 MB | No (prototype sentences) | 85-95% | Semantic understanding; compare input embedding to FOLLOWUP/NEW prototypes; good zero-shot |
| 6 | **qwen2.5:1.5b** | LLM/Ollama | 986 MB | ~1.2 GB | No | 90-100% | Strong middle ground; likely very high accuracy; 1GB savings vs baseline |
| 7 | **smollm2:360m** | LLM/Ollama | 726 MB | ~900 MB | No | 70-85% | HuggingFace optimized; worth testing but instruction following may be weak |
| 8 | **llama3.2:1b** | LLM/Ollama | 1.3 GB | ~1.7 GB | No | 75-90% | Meta's edge model; only modest savings over baseline |
| 9 | **smollm2:135m** | LLM/Ollama | 271 MB | ~400 MB | No | 50-70% | Ultra-tiny; might be too small for reliable classification |
| 10 | **BERT-tiny (fine-tuned)** | ML/Transformer | 17 MB | ~100 MB | Yes | 90-98% | Extremely small after fine-tuning; needs labeled data and training pipeline |
| 11 | **granite3-dense:2b** | LLM/Ollama | 1.6 GB | ~2.0 GB | No | 80-90% | IBM; good instruction following; same size as baseline though |
| 12 | **distilbart-mnli-12-1** | ML/NLI | 600 MB | ~1.2 GB | No (zero-shot) | 80-90% | Zero-shot via NLI; but slow inference and needs transformers runtime |
| 13 | **deepseek-r1:1.5b** | LLM/Ollama | 1.1 GB | ~1.5 GB | No | 60-80% | Reasoning model may overthink binary classification; adds unnecessary chain-of-thought |
| 14 | **tinyllama:1.1b** | LLM/Ollama | 638 MB | ~800 MB | No | 50-70% | 2 years old; only 2K context; weaker instruction following vs newer models |

---

## Top 3 Recommendations to Test First

### 1. qwen2.5:0.5b (LLM, 398 MB)
**Why first**: Smallest modern LLM with strong instruction-following. The Qwen2.5 family specifically improved structured output and instruction adherence. At 398MB, it saves **1.6GB** over the current llama3.2:3B baseline. Drop-in replacement via Ollama -- no code changes needed except the model name. Use with the existing `fewshot` prompt template.

**Test command**: `python test_classifier.py --model qwen2.5:0.5b --verbose`

### 2. qwen3:0.6b (LLM, 523 MB)
**Why second**: Latest generation Qwen with architectural improvements. Supports a `/no_think` mode that skips chain-of-thought reasoning, ideal for fast binary classification. Even their 0.6B "rivals much larger models" per Qwen team benchmarks. Slightly larger than qwen2.5:0.5b but potentially more accurate.

**Test command**: `python test_classifier.py --model qwen3:0.6b --verbose`

### 3. TF-IDF + Logistic Regression (ML, < 1 MB)
**Why third**: We already have 25 labeled examples in `test_classifier.py` (lines 25-56). A TF-IDF + LogReg classifier trained on these (plus ~50-100 more generated examples) would use essentially zero resources (< 1MB model, < 50MB RAM, sub-millisecond inference). This is the **most resource-efficient** option by far. It requires a small Python script to train and serialize the model, then a simple `classify()` function. The main risk is generalization to unseen phrasing, but this can be mitigated by expanding the training set.

**Implementation**: Create `llm/keyword_classifier.py` with sklearn pipeline; train on expanded labeled set; serialize with joblib.

---

## Training Data Requirements Summary

| Approach | Needs Training Data? | How Much? | We Have? |
|----------|---------------------|-----------|----------|
| LLMs via Ollama | No (few-shot in prompt) | N/A | Yes (prompt templates exist) |
| TF-IDF + LogReg/SVM | Yes | 50-200 examples | 25 in test_classifier.py, need ~75 more |
| Keyword Heuristic | No | N/A | N/A |
| all-MiniLM-L6-v2 + Cosine | No (prototype sentences) | ~5-10 prototypes per class | Easy to create |
| BERT-tiny fine-tune | Yes | 100-500 examples | Need to generate |
| distilbart-mnli (zero-shot) | No | N/A | N/A |

---

## Resource Impact Analysis

Running classifier **alongside** the main lamp model (llama3.2:3B fine-tuned, ~2GB):

| Classifier | Additional RAM | Total System RAM | Headroom (of 16GB) |
|------------|---------------|-----------------|---------------------|
| Current (llama3.2:3B) | +2.5 GB | ~4.5 GB | 11.5 GB |
| qwen2.5:0.5b | +600 MB | ~2.6 GB | 13.4 GB |
| qwen3:0.6b | +700 MB | ~2.7 GB | 13.3 GB |
| TF-IDF + LogReg | +50 MB | ~2.05 GB | 13.95 GB |
| Keyword heuristic | +0 MB | ~2.0 GB | 14.0 GB |
| all-MiniLM-L6-v2 | +200 MB | ~2.2 GB | 13.8 GB |

Note: The current baseline uses a separate llama3.2:3B instance for classification, which is the **same model** as the lamp controller. If we switch to a smaller classifier, we free up significant RAM and reduce Ollama's model-swapping overhead.

---

## Key Insight: Ollama Model Swapping
When running two different models via Ollama on the Pi 5, Ollama needs to load/unload models. With the current setup (llama3.2:3B for both classification and lamp control), this isn't an issue since it's the same model. But if we use a **different** smaller model for classification, Ollama would need to swap between the classifier model and the lamp model, which adds latency (~1-3 seconds per swap).

**Mitigation options**:
1. Use Ollama's `OLLAMA_NUM_PARALLEL` or keep both models loaded (needs sufficient RAM)
2. Use an ML approach (TF-IDF/sklearn) that runs outside Ollama entirely -- **no swapping needed**
3. Use Ollama's `--keepalive` flag to keep both models in memory

This model-swapping consideration gives ML approaches (TF-IDF, keyword, sentence-transformers) an additional advantage: they run independently of Ollama and never cause model swaps.

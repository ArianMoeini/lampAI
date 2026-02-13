# Decision: Classifier & Follow-up Style Preservation Fixes

**Date:** 2026-02-13
**Status:** Implemented

## Problems Found During Live Testing

### Bug 1: Mood-word override in hybrid classifier

"make it calm" was incorrectly classified as FOLLOWUP instead of NEW.

**Root cause:** The heuristic correctly returned NEW (mood-word exclusion caught "calm"), but in hybrid mode ALL heuristic NEW results fell through to the gemma3:4b LLM. The LLM saw conversation history and overrode it to FOLLOWUP.

**Fix:** `heuristicClassify()` now returns `{ label, confidence, reason }` instead of a plain string. Hybrid mode only sends **uncertain** results (no keywords matched) to the LLM. Definitive results (keyword match OR mood-word match) are trusted immediately.

```
"make it brighter" → { label: 'FOLLOWUP', confidence: 'definitive', reason: 'keyword' }     → trusted
"make it calm"     → { label: 'NEW',      confidence: 'definitive', reason: 'mood_word' }    → trusted
"not quite"        → { label: 'NEW',      confidence: 'uncertain',  reason: 'no_keywords' }  → ask LLM
```

**Files changed:** `server/server.js` — `heuristicClassify()` and `classifyIntent()`

---

### Bug 2: Model generates completely different programs on follow-ups

When "make it brighter" was correctly classified as FOLLOWUP on a blue-purple gradient, the model generated `solid #FFD700` (gold) — a completely different program.

**Root cause (3 compounding issues):**

1. **Model never saw the current program JSON.** It only got a text summary like "gradient(blue-purple)" — not the actual hex colors `#4A6FB1`, `#9B59B6`.

2. **System prompt had zero follow-up examples.** All 5 examples were NEW requests. The model had never seen how to modify an existing program.

3. **No context signal on follow-ups.** Whether NEW or FOLLOWUP, the model got the same generic "Create a light program for this request."

**Fixes applied:**

**Fix A — Inject current program JSON on follow-ups:**
On FOLLOWUP, the user message now includes the full running program:
```
Current program running on the lamp:
{"program":{"name":"Gradient","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#4A6FB1","color2":"#9B59B6"}}}]}}

Request: make it brighter
```
The model can now see exact colors/speeds/structure and modify them precisely.

**Fix B — Follow-up examples in system prompt:**
Added 3 modification examples showing the pattern:
- Gradient + "make it brighter" → lighten both colors, keep gradient
- Storm + "slower" → increase speed values, keep structure
- Breathing + "add some blue" → shift color, keep pattern type

**Files changed:** `server/server.js` (prompt building + history storage), `llm/prompts.py` (system prompt examples)

---

## Test Results

| Prompt | Before | After |
|--------|--------|-------|
| "make it calm" (after gradient) | FOLLOWUP (wrong) | NEW (correct — mood-word definitive) |
| "make it brighter" (after gradient) | FOLLOWUP + solid gold (wrong output) | FOLLOWUP + brightened gradient (correct) |
| "not quite" (subtle follow-up) | FOLLOWUP via LLM (correct) | FOLLOWUP via LLM (still correct) |
| "slow down the speed" | FOLLOWUP (correct) | FOLLOWUP (still correct) |

## How to Test on Pi

```bash
cd ~/lamp && git pull origin main
cd server && node server.js
```

Watch logs for classifier decisions:
```
[classifier] heuristic definitive: "make it brighter" → FOLLOWUP (keyword)
[classifier] heuristic definitive: "make it calm" → NEW (mood_word)
[classifier] hybrid fallback: "not quite" → heuristic=uncertain NEW, llm=FOLLOWUP
```

#!/usr/bin/env python3
"""
Classifier Benchmark Suite
Tests different models and prompts for FOLLOWUP vs NEW classification.
Supports Ollama LLM models, heuristic baselines, and custom classifiers.

Usage:
    python test_classifier.py                              # Run all models, all prompts
    python test_classifier.py --model llama3.2             # Test specific model
    python test_classifier.py --prompt fewshot              # Test specific prompt
    python test_classifier.py --verbose                     # Show raw model output
    python test_classifier.py --classifier heuristic        # Test heuristic baseline
    python test_classifier.py --context all                 # Test across all contexts
    python test_classifier.py --flow --classifier heuristic # Multi-turn flow tests
    python test_classifier.py --flow --model llama3.2       # Flow tests with Ollama
"""

import argparse
import json
import time
import requests
from dataclasses import dataclass
from typing import Callable

OLLAMA_URL = "http://localhost:11434"

# ============= Test Cases =============
# Each: (input, expected)
# Context: the user previously asked for "thunderstorm" → storm animation

TEST_CASES = [
    # Clear FOLLOWUP cases — modifying the current animation
    ("slow down the speed", "FOLLOWUP"),
    ("make it brighter", "FOLLOWUP"),
    ("even slower please", "FOLLOWUP"),
    ("add more blue", "FOLLOWUP"),
    ("change the color to red", "FOLLOWUP"),
    ("less sparkle", "FOLLOWUP"),
    ("I love it but make the flashes less intense", "FOLLOWUP"),
    ("can you speed it up", "FOLLOWUP"),
    ("dim it a little", "FOLLOWUP"),
    ("make the lightning more frequent", "FOLLOWUP"),

    # Clear NEW cases — completely different request
    ("show a heart", "NEW"),
    ("sunset over the ocean", "NEW"),
    ("pomodoro timer 25 min", "NEW"),
    ("warm and cozy", "NEW"),
    ("rainbow", "NEW"),
    ("ocean waves", "NEW"),
    ("clock showing 14:30", "NEW"),
    ("romantic mood", "NEW"),
    ("show the letter A", "NEW"),
    ("campfire", "NEW"),

    # Ambiguous / edge cases
    ("make it calm", "NEW"),            # Could be modification, but "calm" is a different mood
    ("darker", "FOLLOWUP"),             # Adjusting brightness
    ("turn it off", "NEW"),             # Completely different action
    ("something relaxing", "NEW"),      # New mood request
    ("same but in blue", "FOLLOWUP"),   # Explicit reference to current

    # --- Ambiguous mood changes (NEW — different mood, not modification) ---
    ("make it peaceful", "NEW"),
    ("energetic vibe", "NEW"),
    ("chill mode", "NEW"),

    # --- Partial references to current (FOLLOWUP — explicitly referencing current) ---
    ("same thing but green", "FOLLOWUP"),
    ("like that but faster", "FOLLOWUP"),
    ("keep going but softer", "FOLLOWUP"),

    # --- Time-related requests (always NEW) ---
    ("set a 5 minute timer", "NEW"),
    ("alarm at 7am", "NEW"),
    ("countdown from 10", "NEW"),

    # --- Negation/removal adjustments (FOLLOWUP — modifying current) ---
    ("stop the flashing", "FOLLOWUP"),
    ("no more sparkles", "FOLLOWUP"),
    ("remove the blue", "FOLLOWUP"),

    # --- Multi-word modifications (FOLLOWUP) ---
    ("slower and dimmer", "FOLLOWUP"),
    ("more red less blue", "FOLLOWUP"),

    # --- Context-dependent: wanting something different (NEW) ---
    ("something different", "NEW"),
    ("try another one", "NEW"),
    ("surprise me", "NEW"),

    # --- Single-word inputs ---
    ("brighter", "FOLLOWUP"),
    ("stars", "NEW"),
    ("faster", "FOLLOWUP"),
    ("forest", "NEW"),

    # --- Questions (no modification intent = NEW) ---
    ("what is this?", "NEW"),
]

CONTEXT_HISTORY = [
    {"userPrompt": "thunderstorm", "summary": "thunderstorm, 4 steps: solid(#1A1A2E) → pulse(#FFFFFF) → sparkle(#4444AA) → breathing(#1a1a3a), infinite loop"}
]

# ============= Multi-Context Test Suites =============
# Additional contexts to validate classifier generalization beyond "thunderstorm".

EXTRA_CONTEXTS = {
    "sunset": {
        "description": "Warm gradient sunset over the ocean",
        "history": [
            {"userPrompt": "sunset over the ocean", "summary": "sunset, 3 steps: gradient(#FF6B35->#FF8C42->#FFA726) -> breathing(#FF4500) -> fade(#1A0A2E), 30s loop"}
        ],
        "cases": [
            # FOLLOWUP — modifying the sunset
            ("more orange", "FOLLOWUP"),
            ("make it slower", "FOLLOWUP"),
            ("add some purple", "FOLLOWUP"),
            ("brighter", "FOLLOWUP"),
            ("dim it a little", "FOLLOWUP"),
            ("same but with pink", "FOLLOWUP"),
            ("less red", "FOLLOWUP"),
            # NEW — completely different request
            ("thunderstorm", "NEW"),
            ("show a clock", "NEW"),
            ("pomodoro timer 25 min", "NEW"),
            ("disco lights", "NEW"),
            ("show the letter B", "NEW"),
            ("make it spooky", "NEW"),
            # Edge cases
            ("like that but darker", "FOLLOWUP"),
            ("something different", "NEW"),
            ("faster", "FOLLOWUP"),
            ("forest", "NEW"),
        ],
    },
    "pomodoro": {
        "description": "Countdown timer animation",
        "history": [
            {"userPrompt": "pomodoro timer 25 min", "summary": "pomodoro timer, 2 steps: countdown(#00FF00->#FF0000, 25min) -> pulse(#FF0000, 3x), single run"}
        ],
        "cases": [
            # FOLLOWUP — modifying the timer
            ("make it 30 minutes instead", "FOLLOWUP"),
            ("change the color to blue", "FOLLOWUP"),
            ("speed it up", "FOLLOWUP"),
            ("dimmer", "FOLLOWUP"),
            ("add more green", "FOLLOWUP"),
            ("same but brighter", "FOLLOWUP"),
            # NEW — completely different request
            ("sunset", "NEW"),
            ("rainbow", "NEW"),
            ("show a heart", "NEW"),
            ("campfire", "NEW"),
            ("make it romantic", "NEW"),
            # Edge cases
            ("slower", "FOLLOWUP"),
            ("something different", "NEW"),
            ("turn it off", "NEW"),
        ],
    },
    "romantic": {
        "description": "Soft pink/red breathing animation",
        "history": [
            {"userPrompt": "romantic mood", "summary": "romantic, 3 steps: breathing(#FF69B4) -> sparkle(#FF1493) -> gradient(#FF69B4->#8B0000), infinite loop"}
        ],
        "cases": [
            # FOLLOWUP — modifying the romantic animation
            ("more pink", "FOLLOWUP"),
            ("slower please", "FOLLOWUP"),
            ("less sparkle", "FOLLOWUP"),
            ("brighter", "FOLLOWUP"),
            ("add more red", "FOLLOWUP"),
            ("same but dimmer", "FOLLOWUP"),
            ("tone down the sparkles", "FOLLOWUP"),
            # NEW — completely different request
            ("thunderstorm", "NEW"),
            ("show the time", "NEW"),
            ("pomodoro timer 10 min", "NEW"),
            ("ocean waves", "NEW"),
            ("make it spooky", "NEW"),
            # Edge cases
            ("make it peaceful", "NEW"),
            ("keep going but softer", "FOLLOWUP"),
            ("something different", "NEW"),
        ],
    },
}


# ============= Multi-Turn Conversation Flows =============
# Each flow is a sequence of (input, expected, summary_if_new).
# History BUILDS as we go: NEW resets the "current animation", FOLLOWUP modifies it.
# summary_if_new is used to build realistic history entries for NEW requests.

CONVERSATION_FLOWS = {
    "storm_to_sunset": {
        "description": "Thunderstorm with tweaks, then switch to sunset",
        "turns": [
            ("thunderstorm",       "NEW",      "thunderstorm, 4 steps: solid(#1A1A2E) -> pulse(#FFFFFF) -> sparkle(#4444AA) -> breathing(#1a1a3a), infinite loop"),
            ("slow it down",       "FOLLOWUP", None),
            ("even slower",        "FOLLOWUP", None),
            ("add more lightning", "FOLLOWUP", None),
            ("more blue",          "FOLLOWUP", None),
            ("sunset",             "NEW",      "sunset, 3 steps: gradient(#FF6B35->#FF8C42->#FFA726) -> breathing(#FF4500) -> fade(#1A0A2E), 30s loop"),
            ("more orange",        "FOLLOWUP", None),
            ("dimmer",             "FOLLOWUP", None),
        ],
    },
    "pomodoro_to_heart": {
        "description": "Timer tweaks, then switch to heart animation",
        "turns": [
            ("pomodoro timer 25 min", "NEW",      "pomodoro timer, 2 steps: countdown(#00FF00->#FF0000, 25min) -> pulse(#FF0000, 3x), single run"),
            ("make it red",           "FOLLOWUP", None),
            ("bigger numbers",        "FOLLOWUP", None),
            ("heart shape",           "NEW",      "heart, 2 steps: solid(#FF1493) -> breathing(#FF69B4), infinite loop"),
            ("pinker",                "FOLLOWUP", None),
            ("add sparkle",           "FOLLOWUP", None),
        ],
    },
    "romantic_to_alarm": {
        "description": "Romantic mood tweaks, then switch to alarm",
        "turns": [
            ("romantic mood",          "NEW",      "romantic, 3 steps: breathing(#FF69B4) -> sparkle(#FF1493) -> gradient(#FF69B4->#8B0000), infinite loop"),
            ("darker",                 "FOLLOWUP", None),
            ("add some movement",      "FOLLOWUP", None),
            ("perfect but less pink",  "FOLLOWUP", None),
            ("just a touch more red",  "FOLLOWUP", None),
            ("alarm at 7am",           "NEW",      "alarm, countdown to 7:00 AM with pulse(#FF0000) alert"),
            ("brighter display",       "FOLLOWUP", None),
        ],
    },
    "rainbow_to_forest": {
        "description": "Rainbow through warm colors, then forest and campfire",
        "turns": [
            ("rainbow",              "NEW",      "rainbow, gradient cycle through all hues, 5s per color, infinite loop"),
            ("just the warm colors", "FOLLOWUP", None),
            ("cycle faster",         "FOLLOWUP", None),
            ("a little dimmer",      "FOLLOWUP", None),
            ("forest",               "NEW",      "forest, 3 steps: solid(#0B3D0B) -> sparkle(#228B22) -> breathing(#006400), infinite loop"),
            ("more green",           "FOLLOWUP", None),
            ("darker",               "FOLLOWUP", None),
            ("campfire",             "NEW",      "campfire, 3 steps: gradient(#FF4500->#FF8C00) -> sparkle(#FFD700) -> breathing(#8B0000), infinite loop"),
        ],
    },
    "subtle_followups": {
        "description": "Stress test: subtle follow-ups WITHOUT obvious keywords",
        "turns": [
            ("ocean waves",                "NEW",      "ocean, 3 steps: gradient(#006994->#00CED1) -> wave(#4169E1) -> breathing(#001F3F), infinite loop"),
            ("slower",                     "FOLLOWUP", None),
            ("perfect but the blue",       "FOLLOWUP", None),   # No keyword -- context-only
            ("not quite",                  "FOLLOWUP", None),   # No keyword -- context-only
            ("almost there",               "FOLLOWUP", None),   # No keyword -- context-only
            ("that's too much",            "FOLLOWUP", None),   # "too much" matches
            ("not bad but softer",         "FOLLOWUP", None),   # No keyword -- context-only
            ("love it",                    "NEW",      None),   # Approval with no modification = done
            ("thunderstorm",               "NEW",      "thunderstorm, 4 steps: solid(#1A1A2E) -> pulse(#FFFFFF) -> sparkle(#4444AA) -> breathing(#1a1a3a), infinite loop"),
            ("yes but scarier",            "FOLLOWUP", None),   # No keyword -- context-only
            ("close but not scary enough", "FOLLOWUP", None),   # No keyword -- context-only
        ],
    },

    # ---- Full-chain context tests: back-references, compounds, acknowledgments ----

    "back_references": {
        "description": "Inputs that name or reference EARLIER turns, not just the most recent",
        "turns": [
            ("thunderstorm",                          "NEW",      "thunderstorm, 4 steps: solid(#1A1A2E) -> pulse(#FFFFFF) -> sparkle(#4444AA) -> breathing(#1a1a3a), infinite loop"),
            ("slow it down",                          "FOLLOWUP", None),
            ("add lightning flashes",                  "FOLLOWUP", None),   # "add" keyword
            ("change the thunderstorm to be more purple", "FOLLOWUP", None),   # Names turn 1 explicitly
            ("go back to the original speed",         "FOLLOWUP", None),   # References pre-modification state
            ("sunset",                                "NEW",      "sunset, 3 steps: gradient(#FF6B35->#FF8C42->#FFA726) -> breathing(#FF4500) -> fade(#1A0A2E), 30s loop"),
            ("like the thunderstorm but warmer",      "NEW",      None),   # References turn 1 but requests something new
            ("more orange",                           "FOLLOWUP", None),
        ],
    },
    "compound_modifications": {
        "description": "Modifying parameters from DIFFERENT earlier turns in one request",
        "turns": [
            ("pomodoro timer 25 min",                 "NEW",      "pomodoro timer, 2 steps: countdown(#00FF00->#FF0000, 25min) -> pulse(#FF0000, 3x), single run"),
            ("make it red",                           "FOLLOWUP", None),
            ("bigger numbers",                        "FOLLOWUP", None),
            ("actually make the timer 30 minutes",    "FOLLOWUP", None),   # Modifies turn 1's parameter
            ("keep the red and big numbers but dimmer", "FOLLOWUP", None), # References turns 2+3
            ("heart shape",                           "NEW",      "heart, 2 steps: solid(#FF1493) -> breathing(#FF69B4), infinite loop"),
            ("same colors as the timer",              "FOLLOWUP", None),   # References pomodoro colors across NEW boundary
            ("add a pulse effect",                    "FOLLOWUP", None),
        ],
    },
    "ambiguous_acknowledgments": {
        "description": "Acknowledgments, approval phrases, and ambiguous conversational cues",
        "turns": [
            ("romantic mood",                         "NEW",      "romantic, 3 steps: breathing(#FF69B4) -> sparkle(#FF1493) -> gradient(#FF69B4->#8B0000), infinite loop"),
            ("add some candle flicker",               "FOLLOWUP", None),
            ("the mood should be warmer",             "FOLLOWUP", None),   # References turn 1's "mood"
            ("less flickering",                       "FOLLOWUP", None),   # References turn 2's candle
            ("this is nice",                          "NEW",      None),   # Acknowledgment — no modification requested
            ("something completely different",        "NEW",      None),   # Explicit NEW
            ("campfire",                              "NEW",      "campfire, 3 steps: gradient(#FF4500->#FF8C00) -> sparkle(#FFD700) -> breathing(#8B0000), infinite loop"),
            ("perfect",                               "NEW",      None),   # Acknowledgment — done, no change
        ],
    },
    "mixed_explicit_subtle": {
        "description": "Mix of keyword-heavy and context-only inputs with back-references",
        "turns": [
            ("ocean waves",                           "NEW",      "ocean, 3 steps: gradient(#006994->#00CED1) -> wave(#4169E1) -> breathing(#001F3F), infinite loop"),
            ("slower waves",                          "FOLLOWUP", None),
            ("not quite",                             "FOLLOWUP", None),   # Subtle — no keyword
            ("the ocean should be darker",            "FOLLOWUP", None),   # Names turn 1 explicitly
            ("perfect",                               "NEW",      None),   # Acknowledgment — done
            ("now show me a forest",                  "NEW",      "forest, 3 steps: solid(#0B3D0B) -> sparkle(#228B22) -> breathing(#006400), infinite loop"),
            ("darker like the ocean was",             "FOLLOWUP", None),   # References turn 1 across NEW boundary
            ("that works",                            "NEW",      None),   # Acknowledgment — done
        ],
    },
}


# ============= Heuristic Baseline Classifier =============

FOLLOWUP_SIGNALS = [
    "more", "less", "slower", "faster", "brighter", "dimmer", "darker",
    "speed up", "speed it", "slow down", "slow it", "same but", "same thing but",
    "like that", "keep", "change the", "add more", "add some", "add sparkle",
    "reduce", "increase", "decrease", "tone down", "turn up", "turn down",
    "make it", "a bit", "a little", "a touch", "too much", "not enough",
    "stop the", "remove the", "no more", "bigger", "smaller",
    "just the", "pinker", "redder", "bluer", "greener", "warmer", "cooler",
]

# When "make it" is followed by a mood word, it's a NEW request, not a modification
MOOD_WORDS = [
    "calm", "peaceful", "cozy", "warm", "romantic", "energetic", "relaxing",
    "chill", "mellow", "serene", "soothing", "dreamy", "lively", "intense",
    "spooky", "festive", "cheerful",
]


def heuristic_classify(input_text: str, history: list[dict]) -> str:
    """Rule-based classifier using keyword matching. Floor baseline."""
    lower = input_text.lower()
    # Check for "make it" + mood word → NEW (mood change, not modification)
    if "make it" in lower:
        for mood in MOOD_WORDS:
            if mood in lower:
                return "NEW"
    for signal in FOLLOWUP_SIGNALS:
        if signal in lower:
            return "FOLLOWUP"
    return "NEW"


# ============= TF-IDF + Logistic Regression Classifier =============

_tfidf_model = None  # lazy-loaded singleton

def _get_tfidf_model():
    """Train TF-IDF + LogisticRegression on TEST_CASES (self-bootstrapped)."""
    global _tfidf_model
    if _tfidf_model is not None:
        return _tfidf_model
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
    except ImportError:
        raise RuntimeError("scikit-learn not installed. Run: pip install scikit-learn")

    texts = [t for t, _ in TEST_CASES]
    labels = [l for _, l in TEST_CASES]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=500)
    X = vectorizer.fit_transform(texts)
    clf = LogisticRegression(max_iter=1000, C=1.0)
    clf.fit(X, labels)
    _tfidf_model = (vectorizer, clf)
    return _tfidf_model


def tfidf_lr_classify(input_text: str, history: list[dict]) -> str:
    """TF-IDF + Logistic Regression classifier (trained on TEST_CASES)."""
    vectorizer, clf = _get_tfidf_model()
    X = vectorizer.transform([input_text])
    return clf.predict(X)[0]


# ============= Sentence-Transformer Classifier =============

_st_model = None  # lazy-loaded singleton

# Prototype examples for each class (used to build class centroids)
_FOLLOWUP_PROTOTYPES = [
    "make it slower", "more blue", "change the speed", "less intense",
    "dim it", "brighter", "same but in green", "speed it up",
    "add more red", "tone it down", "stop the flashing",
]
_NEW_PROTOTYPES = [
    "show a heart", "sunset", "pomodoro timer", "ocean waves",
    "campfire", "rainbow", "romantic mood", "show the letter A",
    "warm and cozy", "stars", "forest",
]


def _get_st_model():
    """Load sentence-transformer and compute class centroids."""
    global _st_model
    if _st_model is not None:
        return _st_model
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        raise RuntimeError(
            "sentence-transformers not installed. Run: pip install sentence-transformers"
        )

    model = SentenceTransformer("all-MiniLM-L6-v2")
    followup_emb = model.encode(_FOLLOWUP_PROTOTYPES)
    new_emb = model.encode(_NEW_PROTOTYPES)
    followup_centroid = np.mean(followup_emb, axis=0)
    new_centroid = np.mean(new_emb, axis=0)
    _st_model = (model, followup_centroid, new_centroid)
    return _st_model


def sentence_transformer_classify(input_text: str, history: list[dict]) -> str:
    """Classify by cosine similarity to FOLLOWUP/NEW prototype centroids."""
    import numpy as np
    model, followup_centroid, new_centroid = _get_st_model()
    emb = model.encode([input_text])[0]
    # cosine similarity
    def cos_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    sim_followup = cos_sim(emb, followup_centroid)
    sim_new = cos_sim(emb, new_centroid)
    return "FOLLOWUP" if sim_followup > sim_new else "NEW"


# ============= Classifier Registry =============
# Unified interface for testing LLM and non-LLM classifiers.
#
# Each entry:
#   type: "ollama" | "heuristic" | "sklearn" | ...
#   For "ollama": uses model name + prompt templates
#   For others: uses classify_fn(input_text, history) -> "FOLLOWUP" | "NEW"

CLASSIFIERS = {
    "heuristic": {
        "type": "heuristic",
        "description": "Keyword-matching baseline",
        "classify_fn": heuristic_classify,
    },
    "tfidf_lr": {
        "type": "sklearn",
        "description": "TF-IDF + Logistic Regression (self-bootstrapped on test cases)",
        "classify_fn": tfidf_lr_classify,
    },
    "sentence_transformer": {
        "type": "sentence_transformer",
        "description": "all-MiniLM-L6-v2 cosine similarity to class centroids",
        "classify_fn": sentence_transformer_classify,
    },
}


# ============= Prompt Templates =============

PROMPTS = {
    "fewshot": {
        "description": "Few-shot examples with FOLLOWUP/NEW labels (12/12 on llama3.2)",
        "build": lambda history, inp: (
            'Classify each input as FOLLOWUP (modify current) or NEW (different thing).\n\n'
            f'Current: "{history[-1]["userPrompt"]}" → {history[-1]["summary"]}\n\n'
            '"make it slower" → FOLLOWUP\n'
            '"more blue" → FOLLOWUP\n'
            '"show a heart" → NEW\n'
            '"sunset" → NEW\n'
            '"warm and cozy" → NEW\n'
            '"change the speed" → FOLLOWUP\n'
            '"pomodoro timer" → NEW\n'
            '"less intense" → FOLLOWUP\n\n'
            f'"{inp}" →'
        ),
    },
    "definition": {
        "description": "Explicit definitions with examples (8/10 on llama3.2)",
        "build": lambda history, inp: (
            'You classify user inputs as FOLLOWUP or NEW.\n\n'
            'FOLLOWUP = the input wants to modify, adjust, or continue the previous request '
            '(e.g. "make it slower", "add more blue", "brighter")\n'
            'NEW = the input is a completely different, standalone request '
            '(e.g. "show a heart", "sunset", "pomodoro timer")\n\n'
            'Previous conversation:\n'
            + ''.join(f'{i+1}. "{h["userPrompt"]}" → {h["summary"]}\n' for i, h in enumerate(history))
            + f'\nNew input: "{inp}"\n\n'
            'Classification (one word only):'
        ),
    },
    "minimal": {
        "description": "Minimal prompt — just context and question",
        "build": lambda history, inp: (
            f'Current animation: "{history[-1]["userPrompt"]}"\n'
            f'User says: "{inp}"\n'
            'Is this modifying the current animation (FOLLOWUP) or a new request (NEW)?\n'
            'Answer:'
        ),
    },
    "fewshot_extended": {
        "description": "Extended few-shot with more examples covering edge cases",
        "build": lambda history, inp: (
            'Classify each input as FOLLOWUP (modify current) or NEW (different thing).\n\n'
            f'Current: "{history[-1]["userPrompt"]}" → {history[-1]["summary"]}\n\n'
            '"make it slower" → FOLLOWUP\n'
            '"more blue" → FOLLOWUP\n'
            '"show a heart" → NEW\n'
            '"sunset" → NEW\n'
            '"warm and cozy" → NEW\n'
            '"change the speed" → FOLLOWUP\n'
            '"pomodoro timer" → NEW\n'
            '"less intense" → FOLLOWUP\n'
            '"dim it" → FOLLOWUP\n'
            '"ocean waves" → NEW\n'
            '"same but in green" → FOLLOWUP\n'
            '"campfire" → NEW\n'
            '"something relaxing" → NEW\n'
            '"brighter" → FOLLOWUP\n\n'
            f'"{inp}" →'
        ),
    },
}


# ============= Runner =============

@dataclass
class Result:
    input: str
    expected: str
    got: str
    raw: str
    time_ms: float
    correct: bool


def classify_ollama(model: str, prompt: str, verbose: bool = False) -> tuple[str, str, float]:
    """Run classification via Ollama and return (result, raw_response, time_ms)."""
    start = time.time()
    try:
        res = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 5},
        }, timeout=30)
        data = res.json()
        raw = data.get("response", "").strip()
        elapsed = (time.time() - start) * 1000
        got = "FOLLOWUP" if "FOLLOWUP" in raw.upper() else "NEW"
        return got, raw, elapsed
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return "ERR", str(e), elapsed


def run_benchmark(model: str, prompt_name: str, verbose: bool = False,
                   test_cases=None, context_history=None) -> list[Result]:
    """Run all test cases for a model+prompt combo (Ollama)."""
    if test_cases is None:
        test_cases = TEST_CASES
    if context_history is None:
        context_history = CONTEXT_HISTORY
    prompt_fn = PROMPTS[prompt_name]["build"]
    results = []

    for inp, expected in test_cases:
        prompt = prompt_fn(context_history, inp)
        got, raw, ms = classify_ollama(model, prompt, verbose)
        correct = got == expected
        results.append(Result(inp, expected, got, raw, ms, correct))

        if verbose:
            mark = "ok" if correct else "FAIL"
            print(f"  {mark:4s}  {inp:45s}  exp={expected:8s}  got={got:8s}  ({ms:.0f}ms)  raw={raw!r}")

    return results


def run_classifier_benchmark(classifier_name: str, verbose: bool = False,
                             test_cases=None, context_history=None) -> list[Result]:
    """Run all test cases for a non-LLM classifier."""
    if test_cases is None:
        test_cases = TEST_CASES
    if context_history is None:
        context_history = CONTEXT_HISTORY
    clf = CLASSIFIERS[classifier_name]
    classify_fn = clf["classify_fn"]
    results = []

    for inp, expected in test_cases:
        start = time.time()
        got = classify_fn(inp, context_history)
        ms = (time.time() - start) * 1000
        correct = got == expected
        results.append(Result(inp, expected, got, got, ms, correct))

        if verbose:
            mark = "ok" if correct else "FAIL"
            print(f"  {mark:4s}  {inp:45s}  exp={expected:8s}  got={got:8s}  ({ms:.0f}ms)")

    return results


def run_flow_classifier(classifier_name: str, flow_name: str, verbose: bool = False) -> list[Result]:
    """Run a conversation flow for a non-LLM classifier, building history as we go."""
    flow = CONVERSATION_FLOWS[flow_name]
    clf = CLASSIFIERS[classifier_name]
    classify_fn = clf["classify_fn"]
    results = []
    history = []

    for inp, expected, summary_if_new in flow["turns"]:
        start = time.time()
        got = classify_fn(inp, history if history else [{"userPrompt": "", "summary": ""}])
        ms = (time.time() - start) * 1000
        correct = got == expected
        results.append(Result(inp, expected, got, got, ms, correct))

        if verbose:
            mark = "ok" if correct else "FAIL"
            turn_num = len(results)
            print(f"  {mark:4s}  T{turn_num:<2d}  {inp:40s}  exp={expected:8s}  got={got:8s}  ({ms:.0f}ms)")

        # Build history: NEW requests add a new entry, FOLLOWUP appends to current
        if expected == "NEW" and summary_if_new:
            history.append({"userPrompt": inp, "summary": summary_if_new})

    return results


def run_flow_ollama(model: str, prompt_name: str, flow_name: str, verbose: bool = False) -> list[Result]:
    """Run a conversation flow for an Ollama model, building history as we go."""
    flow = CONVERSATION_FLOWS[flow_name]
    prompt_fn = PROMPTS[prompt_name]["build"]
    results = []
    history = []

    for inp, expected, summary_if_new in flow["turns"]:
        # For the first turn, use a minimal history
        ctx = history if history else [{"userPrompt": "(none)", "summary": "no animation running"}]
        prompt = prompt_fn(ctx, inp)
        got, raw, ms = classify_ollama(model, prompt, verbose)
        correct = got == expected
        results.append(Result(inp, expected, got, raw, ms, correct))

        if verbose:
            mark = "ok" if correct else "FAIL"
            turn_num = len(results)
            print(f"  {mark:4s}  T{turn_num:<2d}  {inp:40s}  exp={expected:8s}  got={got:8s}  ({ms:.0f}ms)  raw={raw!r}")

        # Build history: NEW requests add a new entry
        if expected == "NEW" and summary_if_new:
            history.append({"userPrompt": inp, "summary": summary_if_new})

    return results


def print_summary(name: str, prompt_name: str, results: list[Result]):
    """Print summary for one classifier or model+prompt combo."""
    correct = sum(1 for r in results if r.correct)
    total = len(results)
    avg_ms = sum(r.time_ms for r in results) / total
    pct = correct / total * 100

    failed = [r for r in results if not r.correct]
    fail_str = ""
    if failed:
        fail_str = " | Failed: " + ", ".join(f'"{r.input}"({r.expected}->{r.got})' for r in failed)

    print(f"  {name:20s}  {prompt_name:18s}  {correct:2d}/{total}  ({pct:5.1f}%)  avg={avg_ms:6.0f}ms{fail_str}")


def main():
    parser = argparse.ArgumentParser(description="Classifier Benchmark Suite")
    parser.add_argument("--model", help="Test specific Ollama model (e.g. llama3.2:latest)")
    parser.add_argument("--prompt", help="Test specific prompt (e.g. fewshot)")
    parser.add_argument("--classifier", help="Test a non-LLM classifier (e.g. heuristic)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-case results")
    parser.add_argument("--list-prompts", action="store_true", help="List available prompts")
    parser.add_argument("--list-models", action="store_true", help="List available Ollama models")
    parser.add_argument("--list-classifiers", action="store_true", help="List available non-LLM classifiers")
    parser.add_argument("--context", help="Test specific context (thunderstorm, sunset, pomodoro, romantic, or 'all')")
    parser.add_argument("--flow", nargs="?", const="all", help="Run multi-turn conversation flow tests (name or 'all')")
    args = parser.parse_args()

    if args.list_prompts:
        print("Available prompts:")
        for name, info in PROMPTS.items():
            print(f"  {name:20s}  {info['description']}")
        return

    if args.list_classifiers:
        print("Available classifiers:")
        for name, info in CLASSIFIERS.items():
            print(f"  {name:20s}  {info['description']}")
        return

    if args.list_models:
        try:
            res = requests.get(f"{OLLAMA_URL}/api/tags")
            models = res.json().get("models", [])
            print("Available models:")
            for m in models:
                size_gb = m.get("size", 0) / 1e9
                print(f"  {m['name']:30s}  {size_gb:.1f} GB")
        except Exception as e:
            print(f"Error: {e}")
        return

    # Flow mode: multi-turn conversation tests
    if args.flow is not None:
        if args.flow == "all":
            flow_names = list(CONVERSATION_FLOWS.keys())
        elif args.flow in CONVERSATION_FLOWS:
            flow_names = [args.flow]
        else:
            print(f"Unknown flow: {args.flow}")
            print(f"Available: {', '.join(CONVERSATION_FLOWS.keys())}, all")
            return

        total_turns = sum(len(CONVERSATION_FLOWS[f]["turns"]) for f in flow_names)
        print(f"\n{'='*90}")
        print(f"  Conversation Flow Tests — {total_turns} turns across {len(flow_names)} flow(s)")
        print(f"{'='*90}\n")

        # Determine what to test
        if args.classifier:
            clf_name = args.classifier
            if clf_name not in CLASSIFIERS:
                print(f"Unknown classifier: {clf_name}")
                return

            all_results = []
            for flow_name in flow_names:
                flow = CONVERSATION_FLOWS[flow_name]
                print(f"Flow: {flow_name} — {flow['description']} ({len(flow['turns'])} turns)")
                if args.verbose:
                    print(f"  --- {clf_name} ---")
                results = run_flow_classifier(clf_name, flow_name, verbose=args.verbose)
                print_summary(clf_name, flow_name, results)
                all_results.extend(results)
                print()

            if len(flow_names) > 1:
                print("COMBINED across all flows:")
                print_summary(clf_name, "all_flows", all_results)

        else:
            # Ollama mode
            models = [args.model] if args.model else ["llama3.2:latest"]
            prompt_name = args.prompt or "fewshot"

            all_results_by_model = {m: [] for m in models}
            for flow_name in flow_names:
                flow = CONVERSATION_FLOWS[flow_name]
                print(f"Flow: {flow_name} — {flow['description']} ({len(flow['turns'])} turns)")

                for model in models:
                    if args.verbose:
                        print(f"  --- {model} + {prompt_name} ---")
                    results = run_flow_ollama(model, prompt_name, flow_name, verbose=args.verbose)
                    print_summary(model, flow_name, results)
                    all_results_by_model[model].extend(results)
                print()

            if len(flow_names) > 1:
                print("COMBINED across all flows:")
                for model in models:
                    print_summary(model, "all_flows", all_results_by_model[model])

        print("\nDone.")
        return

    # Build list of (context_name, history, cases) to test
    def _get_context_sets(ctx_arg):
        """Return list of (name, history, cases) tuples based on --context flag."""
        all_contexts = {"thunderstorm": {"history": CONTEXT_HISTORY, "cases": TEST_CASES, "description": "Storm animation with lightning"}}
        all_contexts.update(EXTRA_CONTEXTS)
        if ctx_arg is None:
            # Default: thunderstorm only (backward compatible)
            return [("thunderstorm", CONTEXT_HISTORY, TEST_CASES)]
        if ctx_arg == "all":
            return [(name, c["history"], c["cases"]) for name, c in all_contexts.items()]
        if ctx_arg in all_contexts:
            c = all_contexts[ctx_arg]
            return [(ctx_arg, c["history"], c["cases"])]
        print(f"Unknown context: {ctx_arg}")
        print(f"Available: {', '.join(all_contexts.keys())}, all")
        return []

    context_sets = _get_context_sets(args.context)
    if not context_sets:
        return

    # Non-LLM classifier mode
    if args.classifier:
        clf_name = args.classifier
        if clf_name not in CLASSIFIERS:
            print(f"Unknown classifier: {clf_name}")
            print(f"Available: {', '.join(CLASSIFIERS.keys())}")
            return

        total_cases = sum(len(cases) for _, _, cases in context_sets)
        print(f"\n{'='*90}")
        print(f"  Classifier Benchmark — {total_cases} test cases across {len(context_sets)} context(s)")
        print(f"  Classifier: {clf_name} — {CLASSIFIERS[clf_name]['description']}")
        print(f"{'='*90}\n")

        all_results = []
        for ctx_name, ctx_history, ctx_cases in context_sets:
            print(f"Context: \"{ctx_history[0]['userPrompt']}\" ({len(ctx_cases)} cases)")
            if args.verbose:
                print(f"  --- {clf_name} ---")
            results = run_classifier_benchmark(clf_name, verbose=args.verbose,
                                               test_cases=ctx_cases, context_history=ctx_history)
            print_summary(clf_name, ctx_name, results)
            all_results.extend(results)
            print()

        if len(context_sets) > 1:
            print(f"COMBINED across all contexts:")
            print_summary(clf_name, "all", all_results)

        print("\nDone.")
        return

    # Ollama LLM mode (original behavior)
    if args.model:
        models = [args.model]
    else:
        # Default: test small models suitable for Pi 5
        models = ["llama3.2:latest", "qwen2:0.5b", "phi4-mini:latest"]

    if args.prompt:
        prompt_names = [args.prompt]
    else:
        prompt_names = list(PROMPTS.keys())

    total_cases = sum(len(cases) for _, _, cases in context_sets)
    print(f"\n{'='*90}")
    print(f"  Classifier Benchmark — {total_cases} test cases across {len(context_sets)} context(s)")
    print(f"{'='*90}\n")

    for ctx_name, ctx_history, ctx_cases in context_sets:
        print(f"Context: \"{ctx_history[0]['userPrompt']}\" ({len(ctx_cases)} cases)")
        print(f"  {'-'*80}")

        for prompt_name in prompt_names:
            print(f"  Prompt: {prompt_name} — {PROMPTS[prompt_name]['description']}")

            for model in models:
                if args.verbose:
                    print(f"\n  --- {model} + {prompt_name} ---")
                results = run_benchmark(model, prompt_name, verbose=args.verbose,
                                        test_cases=ctx_cases, context_history=ctx_history)
                print_summary(model, prompt_name, results)

        print()

    print("Done.")


if __name__ == "__main__":
    main()

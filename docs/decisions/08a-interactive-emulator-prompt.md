# Decision: Interactive Emulator Prompt UI

**Date:** 2026-02-12
**Status:** Implemented

## Problem

During development, we needed a way to interactively test the fine-tuned lamp model (lamp-gemma-v2) by typing prompts and seeing real-time results on the HTML5 Canvas emulator.

## Solution

Added a text input + Send button above the lamp emulator that sends prompts to a `/prompt` endpoint on the Node.js server. The server calls Ollama, parses the JSON response, and executes the program on the lamp via the existing scheduler.

## Design Decisions

### Textbox above the emulator (not below)
The lamp is the primary visual output. The prompt input above it creates a natural top-to-bottom flow: input → output. This also mimics how the voice interaction will feel — speaking to the lamp and seeing it respond.

### No model selector dropdown
The fine-tuned model (`lamp-gemma-v2`) is hardcoded. During development, we tested with multiple models but found that only the fine-tuned model produces reliable output. Exposing a dropdown adds complexity without benefit.

### Details toggle overlay
The raw JSON response is hidden by default behind a "Details" button. When opened, it overlays on top of the emulator (position: absolute) rather than pushing the lamp down. This keeps the emulator stable while allowing inspection of the model output.

### JSON repair for truncated output
The fine-tuned model occasionally produces truncated JSON (especially with longer prompts). The server includes `extractJson()` with repair logic:
1. Strip markdown code fences
2. Bracket-counting JSON extraction
3. Truncated JSON repair: strip broken tail, count open brackets, close them

### Loop reference sanitization
The model sometimes generates invalid loop references (e.g., `start_step: "main"` when no step has id "main"). The server maps invalid references to the first/last step IDs.

## Files

- `server/server.js` — `/prompt` endpoint, `extractJson()`, loop sanitization
- `emulator/prompt-client.js` — Client-side prompt logic
- `emulator/index.html` — UI with prompt panel above lamp
- `emulator/styles.css` — Styling for prompt panel and details overlay

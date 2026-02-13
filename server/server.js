/**
 * Moonside Lamp Control Server
 * 
 * Provides:
 * - REST API for controlling LEDs
 * - WebSocket for real-time state broadcast
 */

import express from 'express';
import cors from 'cors';
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import { LedController } from './led-controller.js';
import { PatternEngine } from './patterns.js';
import { ProgramScheduler } from './scheduler.js';
import { GridRenderer } from './renderer.js';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.text());

// Initialize LED controller, pattern engine, and program scheduler
const ledController = new LedController();
const patternEngine = new PatternEngine(ledController);
const renderer = new GridRenderer();

// WebSocket clients
const wsClients = new Set();

// Program scheduler (initialized after broadcast is defined)

// Create HTTP server
const server = createServer(app);

// Create WebSocket server
const wss = new WebSocketServer({ server, path: '/ws' });

wss.on('connection', (ws) => {
    console.log('Client connected');
    wsClients.add(ws);
    
    // Send current state to new client
    ws.send(JSON.stringify({
        type: 'state',
        leds: ledController.getState()
    }));
    
    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data);
            handleWebSocketMessage(ws, message);
        } catch (error) {
            console.error('Invalid message:', error);
        }
    });
    
    ws.on('close', () => {
        console.log('Client disconnected');
        wsClients.delete(ws);
    });
});

// Handle WebSocket messages
function handleWebSocketMessage(ws, message) {
    switch (message.type) {
        case 'getState':
            ws.send(JSON.stringify({
                type: 'state',
                leds: ledController.getState()
            }));
            break;
        default:
            // Forward to all clients (including sender)
            handleCommand(message);
    }
}

// Broadcast to all connected clients
function broadcast(message) {
    const data = JSON.stringify(message);
    for (const client of wsClients) {
        if (client.readyState === 1) { // WebSocket.OPEN
            client.send(data);
        }
    }
}

// Initialize program scheduler (needs handleCommand + broadcast)
const scheduler = new ProgramScheduler(
    (cmd) => handleCommand(cmd),
    (msg) => broadcast(msg)
);

// Handle LED control commands
function handleCommand(command) {
    switch (command.type) {
        case 'led':
            ledController.setLed(command.id, command.color);
            broadcast(command);
            break;
            
        case 'bulk':
            ledController.setBulk(command.leds);
            broadcast(command);
            break;
            
        case 'gradient':
            patternEngine.stop();
            if (command.direction === 'radial' && command.colors.length >= 2) {
                ledController.setRadialGradient(command.colors[0], command.colors[1]);
            } else if (command.colors.length >= 1) {
                ledController.setRadialGradient(command.colors[0], command.colors[0]);
            }
            broadcast({
                type: 'state',
                leds: ledController.getState()
            });
            break;
            
        case 'pattern':
            patternEngine.start(command.name, command.params || {}, (update) => {
                broadcast(update);
            });
            break;
            
        case 'render': {
            // Convert render elements to bulk LED data
            patternEngine.stop();
            const bulkCommand = renderer.render(command.elements || []);
            ledController.setBulk(bulkCommand.leds);
            broadcast(bulkCommand);
            break;
        }

        case 'stop':
            patternEngine.stop();
            broadcast({ type: 'stop' });
            break;
    }
}

// ============= REST API =============

// Health check
app.get('/', (req, res) => {
    res.json({
        name: 'Moonside Lamp Control Server',
        version: '1.0.0',
        endpoints: {
            'GET /state': 'Get current LED state',
            'POST /led/:id': 'Set individual LED color',
            'POST /leds': 'Bulk update LEDs',
            'POST /pattern': 'Start a pattern',
            'POST /gradient': 'Set gradient',
            'POST /stop': 'Stop current pattern'
        }
    });
});

// Get current state
app.get('/state', (req, res) => {
    res.json({
        leds: ledController.getState(),
        activePattern: patternEngine.currentPattern
    });
});

// Set individual LED
app.post('/led/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const color = req.body.color || req.body;
    
    if (isNaN(id) || id < 0 || id >= ledController.totalLeds) {
        return res.status(400).json({ error: 'Invalid LED ID' });
    }
    
    const command = { type: 'led', id, color };
    handleCommand(command);
    
    res.json({ success: true, led: { id, color: ledController.getLed(id) } });
});

// Bulk update LEDs
app.post('/leds', (req, res) => {
    const updates = req.body.leds || req.body;
    
    if (!Array.isArray(updates)) {
        return res.status(400).json({ error: 'Expected array of LED updates' });
    }
    
    const command = { type: 'bulk', leds: updates };
    handleCommand(command);
    
    res.json({ success: true, updated: updates.length });
});

// Set gradient
app.post('/gradient', (req, res) => {
    const { colors, direction = 'radial' } = req.body;
    
    if (!colors || !Array.isArray(colors) || colors.length < 1) {
        return res.status(400).json({ error: 'Expected colors array' });
    }
    
    const command = { type: 'gradient', colors, direction };
    handleCommand(command);
    
    res.json({ success: true, gradient: { colors, direction } });
});

// Start pattern
app.post('/pattern', (req, res) => {
    const { name, params = {} } = req.body;
    
    if (!name) {
        return res.status(400).json({ error: 'Pattern name required' });
    }
    
    const command = { type: 'pattern', name, params };
    handleCommand(command);
    
    res.json({ success: true, pattern: { name, params } });
});

// Stop pattern
app.post('/stop', (req, res) => {
    handleCommand({ type: 'stop' });
    res.json({ success: true });
});

// Solid color shortcut
app.post('/solid', (req, res) => {
    const color = req.body.color || req.body;
    
    const command = { type: 'pattern', name: 'solid', params: { color } };
    handleCommand(command);
    
    res.json({ success: true, color });
});

// ============= Program API =============

// Submit a light program
app.post('/program', (req, res) => {
    const program = req.body.program || req.body;

    if (!program || !program.steps) {
        return res.status(400).json({ error: 'Expected a program with steps' });
    }

    const result = scheduler.start(program);
    if (result.success) {
        res.json(result);
    } else {
        res.status(400).json(result);
    }
});

// Get program status
app.get('/program/status', (req, res) => {
    res.json(scheduler.getStatus());
});

// Pause program
app.post('/program/pause', (req, res) => {
    res.json(scheduler.pause());
});

// Resume program
app.post('/program/resume', (req, res) => {
    res.json(scheduler.resume());
});

// Cancel program
app.post('/program/cancel', (req, res) => {
    res.json(scheduler.cancel());
});

// ============= LLM Prompt API =============

const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434';

// ============= Multi-turn Conversation =============

// Conversation history for multi-turn follow-ups (in-memory, resets on server restart)
// Each entry: { userPrompt, rawResponse, summary, fullUserMsg, fullAssistantMsg }
let conversationHistory = [];
const MAX_EXCHANGES = 10;       // Total exchanges to keep
const FULL_DETAIL_COUNT = 2;    // Last N exchanges kept in full detail (rest summarized)
const CLASSIFIER_MODE = process.env.CLASSIFIER_MODE || 'hybrid'; // 'heuristic', 'llm', or 'hybrid'
const CLASSIFIER_FALLBACK_MODEL = process.env.CLASSIFIER_FALLBACK_MODEL || process.env.CLASSIFIER_MODEL || 'gemma3:4b';
const CLASSIFIER_TIMEOUT_MS = parseInt(process.env.CLASSIFIER_TIMEOUT_MS) || 3000;

// --- Heuristic intent classifier (synced with test_classifier.py FOLLOWUP_SIGNALS) ---
const FOLLOWUP_SIGNALS = [
    // Comparative adjustments
    'more', 'less', 'slower', 'faster', 'brighter', 'dimmer', 'darker',
    'bigger', 'smaller', 'pinker', 'redder', 'bluer', 'greener', 'warmer', 'cooler',
    'yellower', 'oranger', 'purpler', 'whiter', 'softer', 'stronger', 'subtler',
    // Speed/intensity controls
    'speed up', 'speed it', 'slow down', 'slow it', 'tone down', 'turn up', 'turn down',
    'reduce', 'increase', 'decrease',
    // Modification phrases
    'make it', 'same but', 'same thing but', 'like that but', 'keep but',
    'change the', 'switch the', 'swap the', 'flip the',
    'add more', 'add some', 'add sparkle', 'add a', 'throw in',
    'stop the', 'remove the', 'no more', 'get rid of', 'take out', 'drop the',
    'just the', 'only the',
    // Degree qualifiers (imply tweaking)
    'a bit', 'a little', 'a touch', 'a lot', 'slightly', 'way more', 'much more',
    'too much', 'not enough', 'a tad',
    // Approval/disapproval follow-ups
    'not quite', 'almost', 'close but', 'nearly', 'try again',
    'yes but', 'yeah but', 'no but', 'good but', 'nice but', 'love it but',
    'perfect but', 'great but',
    // Short feedback (only meaningful as follow-ups)
    'nah', 'hmm', 'nope', 'meh', 'too dark', 'too bright', 'too fast', 'too slow',
    'not bad', 'keep it', 'keep going',
    // Directional changes
    'go back', 'undo', 'revert', 'previous', 'back to',
    'instead', 'rather', 'actually',
    // Discourse markers & hedged modifications (research-backed)
    'what about', 'how about', 'what if', 'how about we',
    'can you', 'could you', 'can we', 'could we',
    'maybe', 'perhaps', 'possibly',
    // Continuation / additive signals
    'also', 'and also', 'plus', 'on top', 'as well',
    'one more', 'another', 'with that',
    // Comparative questions (imply tweaking current)
    'less of', 'more of', 'any other', 'different color',
    'other color', 'other speed', 'different speed',
];

const NEW_MOOD_WORDS = [
    'calm', 'peaceful', 'cozy', 'warm', 'romantic', 'energetic', 'relaxing',
    'chill', 'mellow', 'serene', 'soothing', 'dreamy', 'lively', 'intense',
    'spooky', 'festive', 'cheerful',
];

function heuristicClassify(input) {
    const lower = input.toLowerCase();
    // "make it <mood>" → definitive NEW (mood change, not modification)
    if (lower.includes('make it')) {
        for (const mood of NEW_MOOD_WORDS) {
            if (lower.includes(mood)) return { label: 'NEW', confidence: 'definitive', reason: 'mood_word' };
        }
    }
    for (const signal of FOLLOWUP_SIGNALS) {
        if (lower.includes(signal)) return { label: 'FOLLOWUP', confidence: 'definitive', reason: 'keyword' };
    }
    // No keywords matched — uncertain, LLM should decide in hybrid mode
    return { label: 'NEW', confidence: 'uncertain', reason: 'no_keywords' };
}

// Summarize a program JSON into a compact description (no LLM needed, deterministic)
function summarizeProgram(prog) {
    if (!prog || !prog.steps) return 'unknown program';
    const parts = [];
    parts.push(prog.name || 'Unnamed');
    const stepDescs = prog.steps.map(s => {
        const cmd = s.command || {};
        if (cmd.type === 'pattern') return `${cmd.name}(${cmd.params?.color || ''})`;
        if (cmd.type === 'render') return `render(${(cmd.elements || []).length} elements)`;
        return cmd.type || '?';
    });
    parts.push(`${prog.steps.length} steps: ${stepDescs.join(' → ')}`);
    if (prog.loop) parts.push(prog.loop.count === 0 ? 'infinite loop' : `${prog.loop.count}x loop`);
    return parts.join(', ');
}

// Build classifier prompt using few-shot examples (12/12 accuracy with llama3.2)
function buildClassifierPrompt(newInput) {
    let prompt = 'Classify each input as FOLLOWUP (modify current) or NEW (different thing).\n\n';

    // Show the current conversation context
    if (conversationHistory.length > 0) {
        const last = conversationHistory[conversationHistory.length - 1];
        prompt += `Current: "${last.userPrompt}" → ${last.summary}\n\n`;
    }

    // Few-shot examples
    prompt += '"make it slower" → FOLLOWUP\n';
    prompt += '"more blue" → FOLLOWUP\n';
    prompt += '"show a heart" → NEW\n';
    prompt += '"sunset" → NEW\n';
    prompt += '"warm and cozy" → NEW\n';
    prompt += '"change the speed" → FOLLOWUP\n';
    prompt += '"pomodoro timer" → NEW\n';
    prompt += '"less intense" → FOLLOWUP\n\n';

    prompt += `"${newInput}" →`;
    return prompt;
}

// LLM classify via Ollama (used by both 'llm' and 'hybrid' modes)
async function llmClassify(newInput) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), CLASSIFIER_TIMEOUT_MS);
    try {
        const res = await fetch(`${OLLAMA_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CLASSIFIER_FALLBACK_MODEL,
                prompt: buildClassifierPrompt(newInput),
                stream: false,
                options: { temperature: 0, num_predict: 5 },
            }),
            signal: controller.signal,
        });
        if (!res.ok) {
            console.warn(`[classifier] LLM error ${res.status}, defaulting to NEW`);
            return 'NEW';
        }
        const data = await res.json();
        const answer = (data.response || '').trim().toUpperCase();
        return answer.includes('FOLLOWUP') ? 'FOLLOWUP' : 'NEW';
    } catch (err) {
        const reason = err.name === 'AbortError' ? 'timeout' : err.message;
        console.warn(`[classifier] LLM failed (${reason}), defaulting to NEW`);
        return 'NEW';
    } finally {
        clearTimeout(timeout);
    }
}

// Classify intent using configured mode:
//   'heuristic' — keyword matching only (<1ms, handles ~90% of inputs correctly)
//   'llm'       — LLM only (slower, handles subtle context-dependent inputs)
//   'hybrid'    — heuristic first; if no FOLLOWUP keyword matched, fall back to LLM
//                 for ambiguous inputs (~10% of traffic). Best of both worlds.
async function classifyIntent(newInput) {
    if (conversationHistory.length === 0) return 'NEW';

    if (CLASSIFIER_MODE === 'llm') {
        return llmClassify(newInput);
    }

    const heuristic = heuristicClassify(newInput);

    if (CLASSIFIER_MODE === 'heuristic') {
        return heuristic.label;
    }

    // Hybrid mode: any definitive result (keyword match OR mood-word match) → trust it
    if (heuristic.confidence === 'definitive') {
        console.log(`[classifier] heuristic definitive: "${newInput}" → ${heuristic.label} (${heuristic.reason})`);
        return heuristic.label;
    }

    // Uncertain heuristic (no keywords matched) — could be a subtle follow-up
    // like "not quite", "almost there", "yes but scarier". Ask the LLM.
    const llmResult = await llmClassify(newInput);
    console.log(`[classifier] hybrid fallback: "${newInput}" → heuristic=uncertain NEW, llm=${llmResult}`);
    return llmResult;
}

// Build the messages array for the main model with tiered history
function buildMainModelMessages(userMessage) {
    const messages = [{ role: 'system', content: LLM_SYSTEM_PROMPT }];

    for (let i = 0; i < conversationHistory.length; i++) {
        const ex = conversationHistory[i];
        const isFull = i >= conversationHistory.length - FULL_DETAIL_COUNT;

        if (isFull) {
            // Recent exchanges: full detail
            messages.push(ex.fullUserMsg);
            messages.push(ex.fullAssistantMsg);
        } else {
            // Older exchanges: summarized into a single user message
            messages.push({ role: 'user', content: `[Previous: "${ex.userPrompt}" → ${ex.summary}]` });
            messages.push({ role: 'assistant', content: '(acknowledged)' });
        }
    }

    messages.push(userMessage);
    return messages;
}

const LLM_SYSTEM_PROMPT = `You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

## Commands (use inside step.command):
- solid(color) — all LEDs one color
  {"type":"pattern","name":"solid","params":{"color":"#FF4444"}}
- gradient(color, color2) — radial blend, center to edge
  {"type":"pattern","name":"gradient","params":{"color":"#FF6B4A","color2":"#FFE4C4"}}
- breathing(color, speed) — pulsing glow. speed in ms (2000=calm, 500=urgent)
  {"type":"pattern","name":"breathing","params":{"color":"#4A90D9","speed":3000}}
- wave(color, color2, speed) — color ripple across rows
  {"type":"pattern","name":"wave","params":{"color":"#FF6B4A","color2":"#FFE4C4","speed":2000}}
- rainbow(speed) — cycling rainbow
  {"type":"pattern","name":"rainbow","params":{"speed":3000}}
- pulse(color, speed) — quick flash then fade, one-shot
  {"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":500}}
- sparkle(color, bgColor, speed, density) — random twinkling
  {"type":"pattern","name":"sparkle","params":{"color":"#FFF","bgColor":"#1a1a1a","speed":100,"density":0.1}}
- render(elements) — draw on the 10×14 grid using drawing tools
  {"type":"render","elements":[{"type":"fill","color":"#000"},{"type":"text","content":"HI","x":2,"y":4,"color":"#FFF"},{"type":"pixel","x":5,"y":1,"color":"#F44"},{"type":"rect","x":0,"y":12,"w":10,"h":2,"color":"#333"}]}
  Drawing tools: fill(color), text(content,x,y,color), pixel(x,y,color), rect(x,y,w,h,color), line(x1,y1,x2,y2,color)
  Grid: 10 wide × 14 tall. x=0 left, y=0 top. Text font: 3px wide per char + 1px gap. Use pixel for custom shapes.
  Combine render with patterns in multi-step programs.

## Program structure:
{"program":{"name":"...","steps":[{"id":"...","command":{...},"duration":ms_or_null}],"loop":{"count":N,"start_step":"id","end_step":"id"},"on_complete":{"command":{...}}}}
- duration: null = stays forever. milliseconds = auto-advance after that time.
- loop: optional. count=0 means infinite. Repeats from start_step to end_step.
- on_complete: optional. Runs when program finishes all steps/loops.

## Timing: 1min=60000, 5min=300000, 25min=1500000, 1hr=3600000. loop.count 0=infinite.

## Color moods:
Warm/cozy: #FF6B4A #FFE4C4 #D88B70 #FFBF00. Calm: #4A90D9 #008B8B #E6E6FA. Focus: #F0F8FF #ADD8E6. Sleep: #191970 #483D8B. Energy: #FF4444 #FF00FF #FFD700. Nature: #228B22 #8B4513. Romantic: #FFB6C1 #9370DB.

## Examples:

User: "warm and cozy"
{"program":{"name":"Warm Cozy","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#D88B70","color2":"#FFF0DC"}},"duration":null}]}}

User: "pomodoro timer 25 min work 5 min break"
{"program":{"name":"Pomodoro","steps":[{"id":"work","command":{"type":"pattern","name":"solid","params":{"color":"#CC3333"}},"duration":1500000},{"id":"break","command":{"type":"pattern","name":"breathing","params":{"color":"#33CC66","speed":4000}},"duration":300000}],"loop":{"count":4,"start_step":"work","end_step":"break"},"on_complete":{"command":{"type":"pattern","name":"rainbow","params":{"speed":2000}}}}}

User: "thunderstorm"
{"program":{"name":"Storm","steps":[{"id":"dark","command":{"type":"pattern","name":"breathing","params":{"color":"#1a1a3a","speed":3000}},"duration":4000},{"id":"flash","command":{"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":300}},"duration":500},{"id":"rumble","command":{"type":"pattern","name":"sparkle","params":{"color":"#4444AA","bgColor":"#0a0a1a","speed":80,"density":0.15}},"duration":3000}],"loop":{"count":0,"start_step":"dark","end_step":"rumble"}}}

User: "clock showing 14:30"
{"program":{"name":"Clock","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#0a0a1a"},{"type":"text","content":"14","x":2,"y":2,"color":"#00FF88"},{"type":"pixel","x":5,"y":7,"color":"#00FF88"},{"type":"pixel","x":5,"y":9,"color":"#00FF88"},{"type":"text","content":"30","x":2,"y":9,"color":"#00FF88"}]},"duration":null}]}}

User: "show a heart"
{"program":{"name":"Heart","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#1a0a1a"},{"type":"pixel","x":3,"y":4,"color":"#FF2266"},{"type":"pixel","x":6,"y":4,"color":"#FF2266"},{"type":"rect","x":2,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":5,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":3,"y":7,"w":4,"h":2,"color":"#FF2266"},{"type":"rect","x":4,"y":9,"w":2,"h":1,"color":"#FF2266"}]},"duration":null}]}}

## Follow-up modifications (when given a current program, adjust it — keep the same structure/pattern, only change what was asked):

Current program: {"program":{"name":"Gradient","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#4A6FB1","color2":"#9B59B6"}},"duration":null}]}}
User: "make it brighter"
{"program":{"name":"Gradient","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#7BA5E8","color2":"#C88FE8"}},"duration":null}]}}

Current program: {"program":{"name":"Storm","steps":[{"id":"dark","command":{"type":"pattern","name":"breathing","params":{"color":"#1a1a3a","speed":3000}},"duration":4000},{"id":"flash","command":{"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":300}},"duration":500}],"loop":{"count":0,"start_step":"dark","end_step":"flash"}}}
User: "slower"
{"program":{"name":"Storm","steps":[{"id":"dark","command":{"type":"pattern","name":"breathing","params":{"color":"#1a1a3a","speed":5000}},"duration":6000},{"id":"flash","command":{"type":"pattern","name":"pulse","params":{"color":"#FFFFFF","speed":300}},"duration":500}],"loop":{"count":0,"start_step":"dark","end_step":"flash"}}}

Current program: {"program":{"name":"Warm Glow","steps":[{"id":"main","command":{"type":"pattern","name":"breathing","params":{"color":"#FF6B4A","speed":4000}},"duration":null}]}}
User: "add some blue"
{"program":{"name":"Warm Glow","steps":[{"id":"main","command":{"type":"pattern","name":"breathing","params":{"color":"#8B5AFF","speed":4000}},"duration":null}]}}`;

function extractJson(text) {
    text = text.trim().replace(/```(?:json)?\s*/g, '').replace(/`+$/, '').trim().replace(/["']+$/, '');
    try { return JSON.parse(text); } catch {}
    const start = text.indexOf('{');
    if (start === -1) return null;
    let depth = 0, inStr = false, esc = false;
    for (let i = start; i < text.length; i++) {
        const c = text[i];
        if (esc) { esc = false; continue; }
        if (c === '\\') { esc = true; continue; }
        if (c === '"') { inStr = !inStr; continue; }
        if (inStr) continue;
        if (c === '{') depth++;
        else if (c === '}') { depth--; if (depth === 0) { try { return JSON.parse(text.slice(start, i + 1)); } catch { return null; } } }
    }
    // Truncated JSON — try to repair by stripping the broken tail and closing brackets
    if (depth > 0) {
        let candidate = text.slice(start);
        // Strip the last incomplete key/value (everything after the last comma or opening bracket)
        candidate = candidate.replace(/,\s*"[^"]*$/, '');       // trailing ,"on_complx
        candidate = candidate.replace(/,\s*"[^"]*":\s*[^,}\]]*$/, ''); // trailing ,"key":val
        candidate = candidate.replace(/,\s*$/, '');              // trailing comma
        // Count remaining open brackets and close them
        let opens = 0, closesNeeded = '';
        let s = false, e = false;
        for (const ch of candidate) {
            if (e) { e = false; continue; }
            if (ch === '\\') { e = true; continue; }
            if (ch === '"') { s = !s; continue; }
            if (s) continue;
            if (ch === '{') opens++;
            else if (ch === '}') opens--;
            else if (ch === '[') closesNeeded += ']';
            else if (ch === ']' && closesNeeded.endsWith(']')) closesNeeded = closesNeeded.slice(0, -1);
        }
        const suffix = closesNeeded.split('').reverse().join('') + '}'.repeat(Math.max(0, opens));
        try {
            console.log('(repaired truncated JSON from LLM)');
            return JSON.parse(candidate + suffix);
        } catch {}
    }
    return null;
}

app.post('/prompt', async (req, res) => {
    const { prompt, model = 'gemma3:4b' } = req.body;
    if (!prompt) return res.status(400).json({ error: 'prompt is required' });

    // Step 1: Classify intent (FOLLOWUP or NEW) using small LLM
    const intent = await classifyIntent(prompt);
    if (intent === 'NEW') {
        conversationHistory = [];
    }
    const turn = conversationHistory.length + 1;
    console.log(`[prompt] "${prompt}" → ${intent} (turn ${turn})`);

    // On follow-ups, inject the current program so the model knows what to modify
    let userContent;
    const lastEntry = conversationHistory.length > 0 ? conversationHistory[conversationHistory.length - 1] : null;
    if (intent === 'FOLLOWUP' && lastEntry?.lastProgram) {
        userContent = `Current program running on the lamp:\n${JSON.stringify({ program: lastEntry.lastProgram }, null, 2)}\n\nRequest: ${prompt}\n\nRespond with ONLY a JSON program. No text.`;
    } else {
        userContent = `Create a light program for this request.\n\nRequest: ${prompt}\n\nRespond with ONLY a JSON program. No text.`;
    }
    const userMessage = { role: 'user', content: userContent };

    try {
        // Step 2: Build messages with tiered history and call main model
        const messages = buildMainModelMessages(userMessage);

        const ollamaRes = await fetch(`${OLLAMA_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model,
                messages,
                stream: false,
                options: { temperature: 0.3, num_predict: 4096 },
            }),
        });

        if (!ollamaRes.ok) {
            return res.status(502).json({ error: `Ollama error: ${ollamaRes.status}` });
        }

        const ollamaData = await ollamaRes.json();
        const raw = ollamaData.message?.content || '';
        const parsed = extractJson(raw);

        if (!parsed) {
            return res.json({ success: false, error: 'Failed to parse JSON from model', raw: raw.slice(0, 500) });
        }

        // Wrap single commands in a program
        let program = parsed;
        if (!program.program && program.type) {
            program = { program: { name: prompt.slice(0, 30), steps: [{ id: 'main', command: program, duration: null }] } };
        }

        // Execute the program on the lamp
        const prog = program.program;
        if (prog && prog.steps) {
            // Sanitize: remove loop if it references non-existent step IDs
            if (prog.loop) {
                const stepIds = new Set(prog.steps.map(s => s.id));
                if (prog.loop.start_step && !stepIds.has(prog.loop.start_step)) {
                    prog.loop.start_step = prog.steps[0].id;
                }
                if (prog.loop.end_step && !stepIds.has(prog.loop.end_step)) {
                    prog.loop.end_step = prog.steps[prog.steps.length - 1].id;
                }
            }
            // Remove null on_complete
            if (prog.on_complete === null) delete prog.on_complete;

            // Step 3: Store in conversation history (tiered)
            conversationHistory.push({
                userPrompt: prompt,
                rawResponse: raw,
                summary: summarizeProgram(prog),
                fullUserMsg: userMessage,
                fullAssistantMsg: { role: 'assistant', content: raw },
                lastProgram: prog,
            });
            // Cap history
            while (conversationHistory.length > MAX_EXCHANGES) {
                conversationHistory.shift();
            }

            const result = scheduler.start(prog);
            return res.json({ success: result.success, program: prog, intent, turn, raw: raw.slice(0, 1000) });
        }

        res.json({ success: false, error: 'No valid program found', raw: raw.slice(0, 500) });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Reset conversation history (programmatic reset)
app.post('/prompt/reset', (req, res) => {
    conversationHistory = [];
    res.json({ success: true });
});

// Start server
server.listen(PORT, () => {
    console.log(`🔮 Moonside Lamp Server running on http://localhost:${PORT}`);
    console.log(`📡 WebSocket available at ws://localhost:${PORT}/ws`);
    console.log(`🧠 Classifier: ${CLASSIFIER_MODE}${CLASSIFIER_MODE !== 'heuristic' ? ` (model=${CLASSIFIER_FALLBACK_MODEL}, timeout=${CLASSIFIER_TIMEOUT_MS}ms)` : ''}`);
    console.log('');
    console.log('Available endpoints:');
    console.log('  GET  /               - API info');
    console.log('  GET  /state          - Current LED state');
    console.log('  POST /led/:id        - Set individual LED');
    console.log('  POST /leds           - Bulk update');
    console.log('  POST /gradient       - Set gradient');
    console.log('  POST /pattern        - Start pattern');
    console.log('  POST /stop           - Stop pattern');
    console.log('  POST /solid          - Set solid color');
    console.log('  POST /program        - Submit light program');
    console.log('  GET  /program/status - Program status');
    console.log('  POST /program/pause  - Pause program');
    console.log('  POST /program/resume - Resume program');
    console.log('  POST /program/cancel - Cancel program');
});

export { app, server, ledController, patternEngine, scheduler };

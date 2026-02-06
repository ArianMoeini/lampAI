/**
 * Video Recording Benchmark
 *
 * Records video of the emulator while running all 21 test prompts
 * through a given Ollama model. Saves one video per model.
 *
 * Usage:
 *   node benchmark_video.js --model gemma3:4b
 *   node benchmark_video.js --model llama3.2
 *   node benchmark_video.js --model phi4-mini
 *   node benchmark_video.js --model qwen3:4b
 *   node benchmark_video.js --model opus  (uses pre-generated programs)
 */

const { chromium } = require('playwright');
const http = require('http');
const path = require('path');
const fs = require('fs');

const LAMP_SERVER = 'http://localhost:3001';
const OLLAMA_URL = 'http://localhost:11434';
const EMULATOR_URL = 'http://localhost:8765';
const RESULTS_DIR = path.join(__dirname, '..', 'benchmark-results2');

const SYSTEM_PROMPT = `You are a lamp programmer. You control a 172-LED lamp (10x14 front grid + 32 ambient back LEDs). Output ONLY a JSON light program. No text, no explanation.

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

## Program structure:
{"program":{"name":"...","steps":[{"id":"...","command":{...},"duration":ms_or_null}],"loop":{"count":N,"start_step":"id","end_step":"id"},"on_complete":{"command":{...}}}}
- duration: null = stays forever. milliseconds = auto-advance after that time.
- loop: optional. count=0 means infinite.
- on_complete: optional. Runs when program finishes all steps/loops.

## Examples:
User: "warm and cozy"
{"program":{"name":"Warm Cozy","steps":[{"id":"main","command":{"type":"pattern","name":"gradient","params":{"color":"#D88B70","color2":"#FFF0DC"}},"duration":null}]}}

User: "show a heart"
{"program":{"name":"Heart","steps":[{"id":"show","command":{"type":"render","elements":[{"type":"fill","color":"#1a0a1a"},{"type":"pixel","x":3,"y":4,"color":"#FF2266"},{"type":"pixel","x":6,"y":4,"color":"#FF2266"},{"type":"rect","x":2,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":5,"y":5,"w":3,"h":2,"color":"#FF2266"},{"type":"rect","x":3,"y":7,"w":4,"h":2,"color":"#FF2266"},{"type":"rect","x":4,"y":9,"w":2,"h":1,"color":"#FF2266"}]},"duration":null}]}}`;

const PROMPTS = [
  { id: 1,  category: 'pixel_art',    prompt: 'show a star' },
  { id: 2,  category: 'pixel_art',    prompt: 'draw a smiley face' },
  { id: 3,  category: 'pixel_art',    prompt: 'show an arrow pointing up' },
  { id: 4,  category: 'pixel_art',    prompt: 'draw a house' },
  { id: 5,  category: 'pixel_art',    prompt: 'show a music note' },
  { id: 6,  category: 'pixel_art',    prompt: 'draw a cat face' },
  { id: 7,  category: 'pixel_art',    prompt: 'show a sun' },
  { id: 8,  category: 'pixel_art',    prompt: 'draw a tree' },
  { id: 9,  category: 'pixel_art',    prompt: 'show a lightning bolt' },
  { id: 10, category: 'pixel_art',    prompt: 'draw a skull' },
  { id: 11, category: 'analog_clock', prompt: 'show an analog clock at 3 o\'clock' },
  { id: 12, category: 'multi_step',   prompt: 'be a pomodoro timer' },
  { id: 13, category: 'multi_step',   prompt: 'simulate a sunrise' },
  { id: 14, category: 'multi_step',   prompt: 'create a meditation session' },
  { id: 15, category: 'multi_step',   prompt: 'party mode' },
  { id: 16, category: 'multi_step',   prompt: 'simulate rain and thunder' },
  { id: 17, category: 'multi_step',   prompt: 'sleep timer that dims over 30 minutes' },
  { id: 18, category: 'multi_step',   prompt: 'countdown from 5' },
  { id: 19, category: 'multi_step',   prompt: 'traffic light sequence' },
  { id: 20, category: 'multi_step',   prompt: 'romantic evening ambiance' },
  { id: 21, category: 'multi_step',   prompt: 'weather display showing sunny and 24 degrees' },
];

// Pre-generated Opus 4.6 programs (loaded from benchmark_opus.py results file if available)
let OPUS_PROGRAMS = null;
try {
  const opusPath = path.join(RESULTS_DIR, 'results_opus.json');
  if (fs.existsSync(opusPath)) {
    OPUS_PROGRAMS = JSON.parse(fs.readFileSync(opusPath, 'utf-8'));
  }
} catch (e) {}

function httpPost(url, data) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const urlObj = new URL(url);
    const req = http.request({
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    }, (res) => {
      let chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
    });
    req.on('error', reject);
    req.setTimeout(120000, () => { req.destroy(); reject(new Error('timeout')); });
    req.write(body);
    req.end();
  });
}

async function queryOllama(prompt, model) {
  const payload = {
    model,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: `Create a light program for this request.\n\nRequest: ${prompt}\n\nRespond with ONLY a JSON program. No text.` },
    ],
    stream: false,
    options: { temperature: 0.3 },
  };
  const res = await httpPost(`${OLLAMA_URL}/api/chat`, payload);
  const result = JSON.parse(res.body);
  return result.message?.content || '';
}

function extractJson(text) {
  text = text.replace(/```(?:json)?\s*/g, '').replace(/`+$/g, '').trim();
  try { return JSON.parse(text); } catch {}
  const start = text.indexOf('{');
  if (start === -1) return null;
  let depth = 0;
  for (let i = start; i < text.length; i++) {
    if (text[i] === '{') depth++;
    else if (text[i] === '}') {
      depth--;
      if (depth === 0) {
        try { return JSON.parse(text.slice(start, i + 1)); } catch { return null; }
      }
    }
  }
  return null;
}

function sendProgram(program) {
  return httpPost(`${LAMP_SERVER}/program`, program)
    .then(r => r.status === 200)
    .catch(() => false);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const args = process.argv.slice(2);
  const modelIdx = args.indexOf('--model');
  const model = modelIdx !== -1 ? args[modelIdx + 1] : 'llama3.2';
  const pauseMs = args.includes('--fast') ? 3000 : 5000;

  const safeName = model.replace(/:/g, '_').replace(/\//g, '_');
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  const videoDir = path.join(RESULTS_DIR, 'videos');
  fs.mkdirSync(videoDir, { recursive: true });

  console.log('='.repeat(60));
  console.log(`  VIDEO BENCHMARK: ${model.toUpperCase()}`);
  console.log(`  Recording emulator at ${EMULATOR_URL}`);
  console.log(`  Pause per test: ${pauseMs / 1000}s`);
  console.log('='.repeat(60));

  // Launch browser with video recording
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    recordVideo: {
      dir: videoDir,
      size: { width: 800, height: 600 },
    },
    viewport: { width: 800, height: 600 },
  });
  const page = await context.newPage();
  await page.goto(EMULATOR_URL);
  await sleep(2000); // Let emulator connect to WebSocket

  const results = [];
  let okCount = 0;

  for (let i = 0; i < PROMPTS.length; i++) {
    const test = PROMPTS[i];
    const { id, category, prompt } = test;

    process.stdout.write(`[${String(i + 1).padStart(2)}/21] ${category.padEnd(14)} | ${prompt}`);

    let program = null;
    let elapsed = 0;
    let status = 'OK';

    if (model === 'opus') {
      // Load from benchmark_opus.py — run the Python script and use its programs
      // For opus, we import the pre-built programs
      try {
        const opusModule = path.join(__dirname, 'benchmark_opus.py');
        // Just use inline Opus programs by running the Python benchmark
        // Actually, let's just send a placeholder — the opus benchmark has its own runner
        process.stdout.write(' (using pre-generated)');
        // We'll call the Python script for opus mode
        const { execSync } = require('child_process');
        const out = execSync(`python3 -c "
import sys; sys.path.insert(0, '${__dirname}')
from benchmark_opus import TEST_CASES
import json
tc = [t for t in TEST_CASES if t['id'] == ${id}][0]
print(json.dumps(tc['program']))
"`, { timeout: 5000 }).toString().trim();
        program = JSON.parse(out);
      } catch (e) {
        status = 'load_error';
        console.log(` FAILED: ${e.message}`);
      }
    } else {
      // Query Ollama
      const t0 = Date.now();
      try {
        const raw = await queryOllama(prompt, model);
        elapsed = (Date.now() - t0) / 1000;
        process.stdout.write(` (${elapsed.toFixed(1)}s)`);
        program = extractJson(raw);
        if (!program) {
          status = 'json_error';
          console.log(` JSON FAIL`);
        }
      } catch (e) {
        elapsed = (Date.now() - t0) / 1000;
        status = 'ollama_error';
        console.log(` ERROR (${elapsed.toFixed(1)}s)`);
      }
    }

    if (program && status === 'OK') {
      // Wrap if needed
      if (!program.program && program.type) {
        program = { program: { name: prompt.slice(0, 30), steps: [{ id: 'main', command: program, duration: null }] } };
      }
      // Cap durations for demo
      const prog = program.program || program;
      for (const step of prog.steps || []) {
        if (typeof step.duration === 'number' && step.duration > 10000) step.duration = 3000;
      }
      const loop = prog.loop;
      if (loop && typeof loop.count === 'number' && (loop.count === 0 || loop.count > 3)) loop.count = 2;

      const ok = await sendProgram(program);
      status = ok ? 'OK' : 'send_error';
      console.log(ok ? ' -> SENT' : ' -> SEND FAILED');
    }

    if (status === 'OK') okCount++;
    results.push({ id, status, prompt, time: elapsed });

    // Wait for the visual to render and be recorded
    if (i < PROMPTS.length - 1) {
      await sleep(pauseMs);
    } else {
      await sleep(2000); // Short wait on last one
    }
  }

  // Close context to finalize video
  const videoPath = await page.video().path();
  await context.close();
  await browser.close();

  // Rename video to model name
  const finalVideoPath = path.join(videoDir, `${safeName}.webm`);
  if (fs.existsSync(videoPath)) {
    fs.renameSync(videoPath, finalVideoPath);
    console.log(`\n  Video saved: ${finalVideoPath}`);
  }

  // Save JSON results
  const jsonPath = path.join(RESULTS_DIR, `results_${safeName}.json`);
  fs.writeFileSync(jsonPath, JSON.stringify({ model, total: 21, ok: okCount, results }, null, 2));

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log(`  SUMMARY (${model})`);
  console.log('='.repeat(60));
  for (const r of results) {
    const sym = r.status === 'OK' ? 'OK  ' : 'FAIL';
    console.log(`  [${String(r.id).padStart(2)}] ${sym} | ${r.prompt}`);
  }
  console.log(`\n  ${okCount}/21 successfully sent to server`);
  console.log(`  Results: ${jsonPath}`);
  console.log(`  Video: ${finalVideoPath}`);
}

main().catch(e => { console.error(e); process.exit(1); });

#!/usr/bin/env node

/**
 * LAMP Benchmark Recorder
 *
 * Records video of each model's benchmark run using Playwright.
 * Spins up a dedicated server on port 3002 so it doesn't interfere
 * with any existing server the user may be running.
 *
 * Usage:
 *   node record.mjs                     # Run all 4 models
 *   node record.mjs --model opus        # Run only one model
 *   node record.mjs --model opus,gpt    # Run specific models
 */

import { chromium } from 'playwright';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LAMP_DIR = path.resolve(__dirname, '..');
const LLM_DIR = path.join(LAMP_DIR, 'llm');
const RESULTS_DIR = path.join(LAMP_DIR, 'benchmark-results');
const EMULATOR_DIR = path.join(LAMP_DIR, 'emulator');
const SERVER_DIR = path.join(LAMP_DIR, 'server');
const SERVER_PORT = 3002;

const ALL_MODELS = [
  { name: 'opus', script: 'benchmark_opus.py', args: ['--fast'] },
  { name: 'gpt', script: 'benchmark_gpt.py', args: ['--fast'] },
  { name: 'llama', script: 'benchmark_llama.py', args: ['--fast'] },
  { name: 'qwen', script: 'benchmark_llama.py', args: ['--fast', '--model', 'qwen3-vl'] },
];

// Parse CLI args
const modelArg = process.argv.find(a => a.startsWith('--model'));
const modelFilter = modelArg
  ? process.argv[process.argv.indexOf(modelArg) + 1]?.split(',')
  : null;
const MODELS = modelFilter
  ? ALL_MODELS.filter(m => modelFilter.includes(m.name))
  : ALL_MODELS;

// Ensure results directory
fs.mkdirSync(RESULTS_DIR, { recursive: true });

// ─── Helpers ────────────────────────────────────────────────

function waitFor(fn, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (fn()) { clearInterval(iv); resolve(); }
      else if (Date.now() - t0 > timeoutMs) { clearInterval(iv); reject(new Error('timeout')); }
    }, 250);
  });
}

function patchScript(scriptName) {
  const src = fs.readFileSync(path.join(LLM_DIR, scriptName), 'utf-8');
  const patched = src.replace(/localhost:3001/g, `localhost:${SERVER_PORT}`);
  const outPath = path.join(RESULTS_DIR, `_tmp_${scriptName}`);
  fs.writeFileSync(outPath, patched);
  return outPath;
}

function runSubprocess(cmd, args, opts = {}) {
  return new Promise((resolve) => {
    const proc = spawn(cmd, args, { ...opts, stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => {
      const t = d.toString();
      stdout += t;
      if (!opts.quiet) process.stdout.write(t);
    });
    proc.stderr.on('data', (d) => {
      const t = d.toString();
      stderr += t;
      if (!opts.quiet) process.stderr.write(t);
    });
    proc.on('close', (code) => resolve({ code, stdout, stderr }));
    proc.on('error', (err) => resolve({ code: -1, stdout, stderr: stderr + err.message }));
  });
}

// ─── Main ───────────────────────────────────────────────────

console.log('');
console.log('='.repeat(56));
console.log('  LAMP BENCHMARK RECORDER');
console.log(`  Models: ${MODELS.map(m => m.name).join(', ')}`);
console.log(`  Server port: ${SERVER_PORT}`);
console.log('='.repeat(56));
console.log('');

// 1) Start dedicated lamp server
console.log('[setup] Starting lamp server...');
let serverReady = false;
const serverProc = spawn('node', ['server.js'], {
  cwd: SERVER_DIR,
  env: { ...process.env, PORT: String(SERVER_PORT) },
  stdio: ['pipe', 'pipe', 'pipe'],
});
serverProc.stdout.on('data', (d) => {
  const t = d.toString();
  if (t.includes('running on')) serverReady = true;
});
serverProc.stderr.on('data', (d) => {
  console.error(`[server] ${d.toString().trim()}`);
});

try {
  await waitFor(() => serverReady, 15000);
  console.log(`[setup] Server running on port ${SERVER_PORT}\n`);
} catch {
  console.error('[setup] FAILED to start server. Exiting.');
  serverProc.kill();
  process.exit(1);
}

// 2) Record each model
const summary = {};

for (let i = 0; i < MODELS.length; i++) {
  const model = MODELS[i];
  console.log('-'.repeat(56));
  console.log(`  [${i + 1}/${MODELS.length}] ${model.name.toUpperCase()}`);
  console.log('-'.repeat(56));

  // Patch benchmark script to use our port
  const patchedScript = patchScript(model.script);

  // Launch Playwright with video recording
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    recordVideo: {
      dir: RESULTS_DIR,
      size: { width: 600, height: 840 },
    },
    viewport: { width: 600, height: 840 },
  });
  const page = await context.newPage();

  // Intercept WebSocket to redirect connections to our port
  await page.addInitScript((port) => {
    const _WS = window.WebSocket;
    window.WebSocket = function (url, ...rest) {
      const fixed = url.replace(/localhost:\d+/, 'localhost:' + port);
      return new _WS(fixed, ...rest);
    };
    window.WebSocket.prototype = _WS.prototype;
    window.WebSocket.CONNECTING = _WS.CONNECTING;
    window.WebSocket.OPEN = _WS.OPEN;
    window.WebSocket.CLOSING = _WS.CLOSING;
    window.WebSocket.CLOSED = _WS.CLOSED;
  }, SERVER_PORT);

  // Load emulator from file
  const emulatorHtml = path.join(EMULATOR_DIR, 'index.html');
  await page.goto(`file://${emulatorHtml}`);
  await page.waitForTimeout(2000); // let emulator init + WS connect

  // Run benchmark subprocess
  const t0 = Date.now();
  const result = await runSubprocess('python3', [patchedScript, ...model.args], {
    cwd: LLM_DIR,
  });
  const duration = ((Date.now() - t0) / 1000).toFixed(1);

  // Let the final animation play out
  await page.waitForTimeout(3000);

  // Save video
  const video = page.video();
  await context.close();
  if (video) {
    try {
      const dest = path.join(RESULTS_DIR, `${model.name}-benchmark.webm`);
      await video.saveAs(dest);
      console.log(`  Video saved: ${model.name}-benchmark.webm`);
    } catch (e) {
      console.log(`  Video save error: ${e.message}`);
    }
  }
  await browser.close();

  // Save text output
  fs.writeFileSync(
    path.join(RESULTS_DIR, `${model.name}-results.txt`),
    result.stdout || '(no output)'
  );

  // Parse summary line: "X/Y successfully sent to server"
  const match = result.stdout.match(/(\d+)\/(\d+) successfully sent/);
  const sent = match ? parseInt(match[1]) : 0;
  const total = match ? parseInt(match[2]) : 21;

  // Count specific errors (for llama/qwen)
  const jsonErrors = (result.stdout.match(/JSON PARSE FAILED/g) || []).length;
  const ollamaErrors = (result.stdout.match(/OLLAMA ERROR/g) || []).length;

  summary[model.name] = {
    sent,
    total,
    jsonErrors,
    ollamaErrors,
    duration: `${duration}s`,
    exitCode: result.code,
  };

  console.log(`  Result: ${sent}/${total} sent (${duration}s)`);
  if (jsonErrors) console.log(`  JSON errors: ${jsonErrors}`);
  if (ollamaErrors) console.log(`  Ollama errors: ${ollamaErrors}`);
  console.log('');

  // Cleanup patched script
  try { fs.unlinkSync(patchedScript); } catch {}
}

// 3) Shutdown
console.log('[cleanup] Stopping server...');
serverProc.kill('SIGTERM');

// 4) Save summary
fs.writeFileSync(
  path.join(RESULTS_DIR, 'summary.json'),
  JSON.stringify(summary, null, 2)
);

// Print final summary
console.log('');
console.log('='.repeat(56));
console.log('  BENCHMARK RESULTS');
console.log('='.repeat(56));
console.log('');
console.log('  Model     Sent   Errors   Duration');
console.log('  ' + '-'.repeat(44));
for (const [name, s] of Object.entries(summary)) {
  const errors = s.jsonErrors + s.ollamaErrors;
  const errStr = errors > 0 ? String(errors) : '-';
  console.log(
    `  ${name.padEnd(10)} ${String(s.sent).padStart(2)}/${s.total}   ${errStr.padStart(4)}     ${s.duration.padStart(7)}`
  );
}
console.log('');
console.log(`  Results: ${RESULTS_DIR}/`);
console.log('='.repeat(56));

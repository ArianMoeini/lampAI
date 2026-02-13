/**
 * Prompt Client — sends natural language prompts to the server's /prompt endpoint
 * and displays the result.
 */

const SERVER_URL = 'http://localhost:3001';
const MODEL = 'lamp-gemma-v2';

const input = document.getElementById('promptInput');
const sendBtn = document.getElementById('promptSend');
const statusEl = document.getElementById('promptStatus');
const detailsBtn = document.getElementById('promptDetails');
const output = document.getElementById('promptOutput');

let lastJson = null;

function setStatus(msg, type = '') {
    statusEl.textContent = msg;
    statusEl.className = 'prompt-status' + (type ? ' ' + type : '');
}

function storeOutput(json) {
    lastJson = json;
    output.textContent = JSON.stringify(json, null, 2);
    detailsBtn.style.display = 'inline-block';
}

function hideAll() {
    output.classList.remove('visible');
    detailsBtn.style.display = 'none';
    detailsBtn.classList.remove('open');
    lastJson = null;
}

detailsBtn.addEventListener('click', () => {
    const isOpen = output.classList.toggle('visible');
    detailsBtn.classList.toggle('open', isOpen);
    detailsBtn.textContent = isOpen ? 'Hide' : 'Details';
});

async function sendPrompt() {
    const prompt = input.value.trim();
    if (!prompt) return;

    sendBtn.disabled = true;
    setStatus('Thinking...');
    hideAll();

    try {
        const res = await fetch(`${SERVER_URL}/prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, model: MODEL }),
        });

        const data = await res.json();

        if (data.success) {
            const prog = data.program;
            const stepCount = prog.steps ? prog.steps.length : 0;
            const intentTag = data.intent === 'FOLLOWUP' ? `follow-up turn ${data.turn}` : 'new';
            setStatus(`${prog.name} (${stepCount} step${stepCount !== 1 ? 's' : ''}) · ${intentTag}`, 'success');
            storeOutput(prog);
        } else {
            setStatus(data.error || 'Failed to generate program', 'error');
            if (data.raw) {
                output.textContent = data.raw;
                detailsBtn.style.display = 'inline-block';
            }
        }
    } catch (err) {
        setStatus(`Error: ${err.message}`, 'error');
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

sendBtn.addEventListener('click', sendPrompt);
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !sendBtn.disabled) sendPrompt();
});

input.focus();

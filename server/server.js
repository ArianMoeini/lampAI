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

// Start server
server.listen(PORT, () => {
    console.log(`🔮 Moonside Lamp Server running on http://localhost:${PORT}`);
    console.log(`📡 WebSocket available at ws://localhost:${PORT}/ws`);
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

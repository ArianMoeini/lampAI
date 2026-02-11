/**
 * Moonside Lamp Emulator - WebSocket Client
 *
 * Connects to the control server to receive program and pattern updates.
 * The emulator starts with its own default gradient; the server only
 * takes over when a program or command is actively sent.
 */

class LampWebSocketClient {
    constructor(lamp, serverUrl = null) {
        this.lamp = lamp;
        this.serverUrl = serverUrl || `ws://localhost:3001/ws`;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000;
        this.activePattern = null; // Track what's running to avoid restarts
        this.hasReceivedCommand = false; // Ignore initial state sync

        this.connect();
    }

    connect() {
        try {
            this.ws = new WebSocket(this.serverUrl);
            this.ws.onopen = () => this.onOpen();
            this.ws.onclose = () => this.onClose();
            this.ws.onerror = () => {};
            this.ws.onmessage = (event) => this.onMessage(event);
        } catch (error) {
            this.scheduleReconnect();
        }
    }

    onOpen() {
        console.log('Connected to lamp server');
        this.reconnectAttempts = 0;
        // Don't request initial state — keep the local default gradient
    }

    onClose() {
        console.log('Disconnected from lamp server');
        this.activePattern = null;
        this.scheduleReconnect();
    }

    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }

    handleMessage(message) {
        switch (message.type) {
            case 'pattern':
                this.hasReceivedCommand = true;
                this.applyPattern(message.name, message.params || {});
                break;

            case 'bulk':
                // Per-frame update from wave/rainbow/sparkle — apply directly
                this.hasReceivedCommand = true;
                this.lamp.stopPattern();
                this.lamp.gradientCenter = null;
                this.lamp.gradientEdge = null;
                this.lamp.applyBulkUpdate(message.leds);
                break;

            case 'state':
                // Ignore the automatic state sync on connect — keep local gradient.
                // Only apply state if we've already received a command this session.
                if (this.hasReceivedCommand && message.leds && Array.isArray(message.leds)) {
                    this.lamp.stopPattern();
                    this.lamp.gradientCenter = null;
                    this.lamp.gradientEdge = null;
                    this.lamp.applyBulkUpdate(message.leds);
                }
                break;

            case 'stop':
                this.lamp.stopPattern();
                this.activePattern = null;
                break;

            case 'program_status':
                if (message.event) {
                    console.log(`Program: ${message.event}`, message.program_name || '');
                }
                break;
        }
    }

    applyPattern(name, params) {
        const color = params.color || '#FF6B4A';
        const color2 = params.color2 || '#FFE4C4';
        const speed = params.speed || 2000;

        switch (name) {
            case 'solid':
                this.lamp.stopPattern();
                this.lamp.setSolidColor(color);
                this.activePattern = null;
                break;

            case 'gradient':
                this.lamp.stopPattern();
                this.lamp.setRadialGradient(color, color2);
                this.activePattern = null;
                break;

            case 'breathing':
                // Server sends per-frame breathing updates. Start local animation
                // only once, then ignore subsequent frames.
                if (this.activePattern !== 'breathing') {
                    this.lamp.startBreathing(color, speed);
                    this.activePattern = 'breathing';
                }
                break;

            case 'wave':
                if (this.activePattern !== 'wave') {
                    this.lamp.startWave(color, color2, speed);
                    this.activePattern = 'wave';
                }
                break;

            case 'rainbow':
                if (this.activePattern !== 'rainbow') {
                    this.lamp.startRainbow(speed);
                    this.activePattern = 'rainbow';
                }
                break;

            case 'pulse':
                // Pulse is one-shot, always apply
                this.lamp.stopPattern();
                this.lamp.setSolidColor(color);
                this.activePattern = null;
                break;

            case 'sparkle':
                // Sparkle comes as bulk updates from the server
                // but if we get a pattern message, start it
                this.activePattern = 'sparkle';
                break;

            default:
                console.log('Unknown pattern:', name);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.min(this.reconnectAttempts, 5);
            setTimeout(() => this.connect(), delay);
        }
    }
}

// Initialize WebSocket client after lamp is ready
document.addEventListener('DOMContentLoaded', () => {
    const checkLamp = setInterval(() => {
        if (window.lamp) {
            clearInterval(checkLamp);
            window.wsClient = new LampWebSocketClient(window.lamp);
        }
    }, 100);
});

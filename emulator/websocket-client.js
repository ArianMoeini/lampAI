/**
 * Moonside Lamp Emulator - WebSocket Client
 * 
 * Connects to the control server and applies real-time LED updates
 */

class LampWebSocketClient {
    constructor(lamp, serverUrl = null) {
        this.lamp = lamp;
        this.serverUrl = serverUrl || this.getDefaultServerUrl();
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        
        // UI elements
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        
        // Auto-connect
        this.connect();
    }
    
    getDefaultServerUrl() {
        // Default to localhost on port 3001
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//localhost:3001/ws`;
    }
    
    connect() {
        try {
            this.updateStatus('connecting');
            this.ws = new WebSocket(this.serverUrl);
            
            this.ws.onopen = () => this.onOpen();
            this.ws.onclose = () => this.onClose();
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onmessage = (event) => this.onMessage(event);
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }
    
    onOpen() {
        console.log('Connected to lamp server');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateStatus('connected');
        
        // Request current state
        this.send({ type: 'getState' });
    }
    
    onClose() {
        console.log('Disconnected from lamp server');
        this.isConnected = false;
        this.updateStatus('disconnected');
        this.scheduleReconnect();
    }
    
    onError(error) {
        console.error('WebSocket error:', error);
        this.updateStatus('error');
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
            case 'led':
                // Individual LED update
                this.lamp.setLed(message.id, message.color);
                break;
                
            case 'bulk':
                // Bulk LED update
                this.lamp.stopPattern();
                this.lamp.applyBulkUpdate(message.leds);
                break;
                
            case 'gradient':
                // Apply gradient
                this.lamp.stopPattern();
                if (message.direction === 'radial') {
                    this.lamp.setRadialGradient(message.colors[0], message.colors[1] || message.colors[0]);
                }
                break;
                
            case 'pattern':
                // Start pattern
                this.applyPattern(message.name, message.params || {});
                break;
                
            case 'state':
                // Full state sync
                this.lamp.stopPattern();
                if (message.leds && Array.isArray(message.leds)) {
                    this.lamp.applyBulkUpdate(message.leds);
                }
                break;
                
            case 'stop':
                // Stop current pattern
                this.lamp.stopPattern();
                break;
                
            default:
                console.log('Unknown message type:', message.type);
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
                break;
            case 'gradient':
                this.lamp.stopPattern();
                this.lamp.setRadialGradient(color, color2);
                break;
            case 'breathing':
                this.lamp.startBreathing(color, speed);
                break;
            case 'wave':
                this.lamp.startWave(color, color2, speed);
                break;
            case 'rainbow':
                this.lamp.startRainbow(speed);
                break;
            default:
                console.log('Unknown pattern:', name);
        }
    }
    
    send(message) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.min(this.reconnectAttempts, 5);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.log('Max reconnection attempts reached');
            this.updateStatus('failed');
        }
    }
    
    updateStatus(status) {
        if (!this.statusDot || !this.statusText) return;
        
        this.statusDot.classList.remove('connected');
        
        switch (status) {
            case 'connected':
                this.statusDot.classList.add('connected');
                this.statusText.textContent = 'Connected';
                break;
            case 'connecting':
                this.statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
                this.statusText.textContent = 'Disconnected';
                break;
            case 'error':
                this.statusText.textContent = 'Connection Error';
                break;
            case 'failed':
                this.statusText.textContent = 'Connection Failed';
                break;
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Initialize WebSocket client when lamp is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for lamp to be initialized
    const checkLamp = setInterval(() => {
        if (window.lamp) {
            clearInterval(checkLamp);
            window.wsClient = new LampWebSocketClient(window.lamp);
        }
    }, 100);
});

// Export for external use
window.LampWebSocketClient = LampWebSocketClient;

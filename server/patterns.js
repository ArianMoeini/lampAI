/**
 * Pattern Engine - Handles animated LED patterns
 * 
 * Available patterns:
 * - solid: Single color for all LEDs
 * - gradient: Radial gradient (static)
 * - breathing: Pulsing brightness
 * - wave: Color wave across rows
 * - rainbow: Cycling rainbow colors
 * - pulse: Quick flash and fade
 * - sparkle: Random twinkling LEDs
 */

export class PatternEngine {
    constructor(ledController) {
        this.ledController = ledController;
        this.currentPattern = null;
        this.intervalId = null;
        this.animationFrame = 0;
    }
    
    start(patternName, params, broadcastFn) {
        this.stop();
        this.currentPattern = patternName;
        this.animationFrame = 0;
        this.broadcastFn = broadcastFn;
        
        switch (patternName) {
            case 'solid':
                this.runSolid(params);
                break;
            case 'gradient':
                this.runGradient(params);
                break;
            case 'breathing':
                this.runBreathing(params);
                break;
            case 'wave':
                this.runWave(params);
                break;
            case 'rainbow':
                this.runRainbow(params);
                break;
            case 'pulse':
                this.runPulse(params);
                break;
            case 'sparkle':
                this.runSparkle(params);
                break;
            default:
                console.log(`Unknown pattern: ${patternName}`);
        }
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.currentPattern = null;
    }
    
    broadcast(message) {
        if (this.broadcastFn) {
            this.broadcastFn(message);
        }
    }
    
    // ============= Pattern Implementations =============
    
    runSolid(params) {
        const color = params.color || '#FF6B4A';
        this.ledController.setSolidColor(color);
        this.broadcast({
            type: 'pattern',
            name: 'solid',
            params: { color }
        });
    }
    
    runGradient(params) {
        const color = params.color || '#FF6B4A';
        const color2 = params.color2 || '#FFE4C4';
        this.ledController.setRadialGradient(color, color2);
        this.broadcast({
            type: 'pattern',
            name: 'gradient',
            params: { color, color2 }
        });
    }
    
    runBreathing(params) {
        const color = params.color || '#FF6B4A';
        const speed = params.speed || 2000;
        const baseColor = this.hexToRgb(color);
        
        const frameInterval = 50; // 20 FPS
        const totalFrames = speed / frameInterval;
        
        this.intervalId = setInterval(() => {
            this.animationFrame = (this.animationFrame + 1) % totalFrames;
            const t = this.animationFrame / totalFrames;
            const brightness = 0.3 + (Math.sin(t * Math.PI * 2) + 1) / 2 * 0.7;
            
            const adjustedColor = this.rgbToHex(
                baseColor.r * brightness,
                baseColor.g * brightness,
                baseColor.b * brightness
            );
            
            this.ledController.setSolidColor(adjustedColor);
            this.broadcast({
                type: 'pattern',
                name: 'breathing',
                params: { color: adjustedColor, speed }
            });
        }, frameInterval);
    }
    
    runWave(params) {
        const color1 = params.color || '#FF6B4A';
        const color2 = params.color2 || '#FFE4C4';
        const speed = params.speed || 2000;
        const rgb1 = this.hexToRgb(color1);
        const rgb2 = this.hexToRgb(color2);
        
        const frameInterval = 50;
        const totalFrames = speed / frameInterval;
        
        this.intervalId = setInterval(() => {
            this.animationFrame = (this.animationFrame + 1) % totalFrames;
            const phase = (this.animationFrame / totalFrames) * Math.PI * 2;
            
            const updates = [];
            for (let row = 0; row < this.ledController.rows; row++) {
                const t = (Math.sin(phase + row * 0.5) + 1) / 2;
                const color = this.lerpColorHex(rgb1, rgb2, t);
                
                for (let col = 0; col < this.ledController.cols; col++) {
                    const id = row * this.ledController.cols + col;
                    updates.push({ id, color });
                }
            }
            
            // Ambient LEDs
            const avgColor = this.lerpColorHex(rgb1, rgb2, 0.5);
            for (let i = this.ledController.frontLedCount; i < this.ledController.totalLeds; i++) {
                updates.push({ id: i, color: avgColor });
            }
            
            this.ledController.setBulk(updates);
            this.broadcast({
                type: 'bulk',
                leds: updates
            });
        }, frameInterval);
    }
    
    runRainbow(params) {
        const speed = params.speed || 3000;
        
        const frameInterval = 50;
        const totalFrames = speed / frameInterval;
        
        this.intervalId = setInterval(() => {
            this.animationFrame = (this.animationFrame + 1) % totalFrames;
            const baseHue = this.animationFrame / totalFrames;
            
            const updates = [];
            for (let row = 0; row < this.ledController.rows; row++) {
                for (let col = 0; col < this.ledController.cols; col++) {
                    const hue = (baseHue + row / this.ledController.rows * 0.3 + col / this.ledController.cols * 0.1) % 1;
                    const color = this.hslToHex(hue, 0.8, 0.6);
                    const id = row * this.ledController.cols + col;
                    updates.push({ id, color });
                }
            }
            
            // Ambient LEDs follow base hue
            const ambientColor = this.hslToHex(baseHue, 0.7, 0.5);
            for (let i = this.ledController.frontLedCount; i < this.ledController.totalLeds; i++) {
                updates.push({ id: i, color: ambientColor });
            }
            
            this.ledController.setBulk(updates);
            this.broadcast({
                type: 'bulk',
                leds: updates
            });
        }, frameInterval);
    }
    
    runPulse(params) {
        const color = params.color || '#FFFFFF';
        const speed = params.speed || 500;
        const baseColor = this.hexToRgb(color);
        
        const frameInterval = 30;
        const totalFrames = speed / frameInterval;
        let frame = 0;
        
        this.intervalId = setInterval(() => {
            frame++;
            const t = frame / totalFrames;
            
            if (t >= 1) {
                this.stop();
                return;
            }
            
            // Quick rise, slow fall
            const brightness = t < 0.2 ? t / 0.2 : 1 - (t - 0.2) / 0.8;
            
            const adjustedColor = this.rgbToHex(
                baseColor.r * brightness,
                baseColor.g * brightness,
                baseColor.b * brightness
            );
            
            this.ledController.setSolidColor(adjustedColor);
            this.broadcast({
                type: 'pattern',
                name: 'pulse',
                params: { color: adjustedColor }
            });
        }, frameInterval);
    }
    
    runSparkle(params) {
        const color = params.color || '#FFFFFF';
        const bgColor = params.bgColor || '#1a1a1a';
        const speed = params.speed || 100;
        const density = params.density || 0.1;
        
        this.intervalId = setInterval(() => {
            const updates = [];
            
            for (let i = 0; i < this.ledController.frontLedCount; i++) {
                if (Math.random() < density) {
                    updates.push({ id: i, color });
                } else if (Math.random() < 0.3) {
                    updates.push({ id: i, color: bgColor });
                }
            }
            
            if (updates.length > 0) {
                this.ledController.setBulk(updates);
                this.broadcast({
                    type: 'bulk',
                    leds: updates
                });
            }
        }, speed);
    }
    
    // ============= Color Utilities =============
    
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }
    
    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = Math.round(Math.max(0, Math.min(255, x))).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    lerpColorHex(color1, color2, t) {
        const r = Math.round(color1.r + (color2.r - color1.r) * t);
        const g = Math.round(color1.g + (color2.g - color1.g) * t);
        const b = Math.round(color1.b + (color2.b - color1.b) * t);
        return this.rgbToHex(r, g, b);
    }
    
    hslToHex(h, s, l) {
        let r, g, b;
        
        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
        
        return this.rgbToHex(r * 255, g * 255, b * 255);
    }
}

export default PatternEngine;

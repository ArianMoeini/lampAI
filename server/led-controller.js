/**
 * LED Controller - Manages state for all 172 LEDs
 * 
 * LED Layout:
 * - Front Display: 140 LEDs (10 columns x 14 rows), IDs 0-139
 * - Back Ambient: 32 LEDs (8 per side), IDs 140-171
 */

export class LedController {
    constructor() {
        this.cols = 10;
        this.rows = 14;
        this.frontLedCount = this.cols * this.rows; // 140
        this.backLedCount = 32;
        this.totalLeds = this.frontLedCount + this.backLedCount; // 172
        
        // Initialize all LEDs to off (black)
        this.leds = new Array(this.totalLeds).fill(null).map(() => '#000000');
        
        // Set default warm gradient
        this.setRadialGradient('#FF6B4A', '#FFE4C4');
    }
    
    // Get LED color by ID
    getLed(id) {
        if (id >= 0 && id < this.totalLeds) {
            return this.leds[id];
        }
        return null;
    }
    
    // Set individual LED
    setLed(id, color) {
        if (id >= 0 && id < this.totalLeds) {
            this.leds[id] = this.normalizeColor(color);
            return true;
        }
        return false;
    }
    
    // Set multiple LEDs at once
    setBulk(updates) {
        for (const update of updates) {
            this.setLed(update.id, update.color);
        }
    }
    
    // Set all LEDs to one color
    setSolidColor(color) {
        const normalizedColor = this.normalizeColor(color);
        for (let i = 0; i < this.totalLeds; i++) {
            this.leds[i] = normalizedColor;
        }
    }
    
    // Set radial gradient
    setRadialGradient(centerColor, edgeColor) {
        const center = this.hexToRgb(centerColor);
        const edge = this.hexToRgb(edgeColor);
        
        const centerX = this.cols / 2;
        const centerY = this.rows / 2;
        const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);
        
        // Front LEDs
        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                const dx = col - centerX + 0.5;
                const dy = row - centerY + 0.5;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const t = dist / maxDist;
                
                const id = row * this.cols + col;
                this.leds[id] = this.lerpColorHex(center, edge, t);
            }
        }
        
        // Back ambient LEDs - use blend
        const ambientColor = this.lerpColorHex(center, edge, 0.5);
        for (let i = this.frontLedCount; i < this.totalLeds; i++) {
            this.leds[i] = ambientColor;
        }
    }
    
    // Get full state
    getState() {
        return this.leds.map((color, id) => ({ id, color }));
    }
    
    // Normalize color to hex format
    normalizeColor(color) {
        if (typeof color === 'string') {
            if (color.startsWith('#')) {
                return color.toLowerCase();
            }
            // Handle rgb() format
            const rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
            if (rgbMatch) {
                return this.rgbToHex(
                    parseInt(rgbMatch[1]),
                    parseInt(rgbMatch[2]),
                    parseInt(rgbMatch[3])
                );
            }
        } else if (typeof color === 'object' && color.r !== undefined) {
            return this.rgbToHex(color.r, color.g, color.b);
        }
        return '#000000';
    }
    
    // Convert hex to RGB
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }
    
    // Convert RGB to hex
    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = Math.round(Math.max(0, Math.min(255, x))).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    // Interpolate between two colors
    lerpColorHex(color1, color2, t) {
        const r = Math.round(color1.r + (color2.r - color1.r) * t);
        const g = Math.round(color1.g + (color2.g - color1.g) * t);
        const b = Math.round(color1.b + (color2.b - color1.b) * t);
        return this.rgbToHex(r, g, b);
    }
}

export default LedController;

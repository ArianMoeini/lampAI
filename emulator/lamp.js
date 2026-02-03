/**
 * Moonside Lamp Emulator - LED Visualization
 *
 * LED Layout:
 * - Front Display: 140 LEDs (10 columns x 14 rows), IDs 0-139
 * - Back Ambient: 32 LEDs (8 per side), IDs 140-171
 */

class LampEmulator {
    constructor(canvasId, ambientGlowId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.ambientGlow = document.getElementById(ambientGlowId);

        // LED configuration
        this.cols = 10;
        this.rows = 14;
        this.frontLedCount = this.cols * this.rows; // 140
        this.backLedCount = 32;
        this.totalLeds = this.frontLedCount + this.backLedCount; // 172

        // LED state (RGBA values)
        this.leds = new Array(this.totalLeds).fill(null).map(() => ({ r: 0, g: 0, b: 0 }));

        // Gradient state for smooth rendering
        this.gradientCenter = null;
        this.gradientEdge = null;

        // Animation state
        this.animationId = null;
        this.currentPattern = null;
        this.patternStartTime = 0;

        // Initialize canvas size
        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Start render loop
        this.render();

        // Set default gradient matching the real lamp
        this.setRadialGradient('#D88B70', '#FFF0DC');
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        this.displayWidth = rect.width;
        this.displayHeight = rect.height;
    }

    // Convert hex color to RGB object
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
            const hex = Math.round(x).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }

    // Interpolate between two colors
    lerpColor(color1, color2, t) {
        return {
            r: color1.r + (color2.r - color1.r) * t,
            g: color1.g + (color2.g - color1.g) * t,
            b: color1.b + (color2.b - color1.b) * t
        };
    }

    // Set individual LED
    setLed(id, color) {
        if (id >= 0 && id < this.totalLeds) {
            this.leds[id] = typeof color === 'string' ? this.hexToRgb(color) : color;
        }
    }

    // Set all LEDs to one color
    setSolidColor(hex) {
        this.gradientCenter = null;
        this.gradientEdge = null;
        const color = this.hexToRgb(hex);
        for (let i = 0; i < this.totalLeds; i++) {
            this.leds[i] = { ...color };
        }
        this.updateAmbientGlow(color);
    }

    // Set radial gradient (center color, edge color)
    setRadialGradient(centerHex, edgeHex) {
        const centerColor = this.hexToRgb(centerHex);
        const edgeColor = this.hexToRgb(edgeHex);

        // Store gradient colors for smooth canvas rendering
        this.gradientCenter = centerColor;
        this.gradientEdge = edgeColor;

        const centerX = this.cols / 2;
        const centerY = this.rows / 2;
        const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                const dx = col - centerX + 0.5;
                const dy = row - centerY + 0.5;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const t = dist / maxDist;

                const id = row * this.cols + col;
                this.leds[id] = this.lerpColor(centerColor, edgeColor, t);
            }
        }

        // Set ambient LEDs to blend of both colors
        const ambientColor = this.lerpColor(centerColor, edgeColor, 0.5);
        for (let i = this.frontLedCount; i < this.totalLeds; i++) {
            this.leds[i] = { ...ambientColor };
        }

        this.updateAmbientGlow(ambientColor);
    }

    // Update ambient glow effect
    updateAmbientGlow(color) {
        const rgba = `rgba(${Math.round(color.r)}, ${Math.round(color.g)}, ${Math.round(color.b)}, 0.4)`;
        this.ambientGlow.style.background = `radial-gradient(ellipse at center, ${rgba} 0%, transparent 70%)`;
    }

    // Breathing animation
    startBreathing(hex, speed = 2000) {
        this.stopPattern();
        this.gradientCenter = null;
        this.gradientEdge = null;
        const color = this.hexToRgb(hex);
        this.currentPattern = 'breathing';
        this.patternStartTime = performance.now();

        const animate = () => {
            const elapsed = performance.now() - this.patternStartTime;
            const t = (Math.sin(elapsed * Math.PI * 2 / speed) + 1) / 2;
            const brightness = 0.3 + t * 0.7;

            const adjustedColor = {
                r: color.r * brightness,
                g: color.g * brightness,
                b: color.b * brightness
            };

            for (let i = 0; i < this.totalLeds; i++) {
                this.leds[i] = { ...adjustedColor };
            }
            this.updateAmbientGlow(adjustedColor);

            if (this.currentPattern === 'breathing') {
                this.animationId = requestAnimationFrame(animate);
            }
        };

        animate();
    }

    // Wave animation
    startWave(hex1, hex2, speed = 2000) {
        this.stopPattern();
        this.gradientCenter = null;
        this.gradientEdge = null;
        const color1 = this.hexToRgb(hex1);
        const color2 = this.hexToRgb(hex2);
        this.currentPattern = 'wave';
        this.patternStartTime = performance.now();

        const animate = () => {
            const elapsed = performance.now() - this.patternStartTime;
            const phase = (elapsed / speed) * Math.PI * 2;

            for (let row = 0; row < this.rows; row++) {
                for (let col = 0; col < this.cols; col++) {
                    const t = (Math.sin(phase + row * 0.5) + 1) / 2;
                    const id = row * this.cols + col;
                    this.leds[id] = this.lerpColor(color1, color2, t);
                }
            }

            // Ambient follows average
            const avgColor = this.lerpColor(color1, color2, 0.5);
            for (let i = this.frontLedCount; i < this.totalLeds; i++) {
                this.leds[i] = { ...avgColor };
            }
            this.updateAmbientGlow(avgColor);

            if (this.currentPattern === 'wave') {
                this.animationId = requestAnimationFrame(animate);
            }
        };

        animate();
    }

    // Rainbow animation
    startRainbow(speed = 3000) {
        this.stopPattern();
        this.gradientCenter = null;
        this.gradientEdge = null;
        this.currentPattern = 'rainbow';
        this.patternStartTime = performance.now();

        const hslToRgb = (h, s, l) => {
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
            return { r: r * 255, g: g * 255, b: b * 255 };
        };

        const animate = () => {
            const elapsed = performance.now() - this.patternStartTime;
            const baseHue = (elapsed / speed) % 1;

            for (let row = 0; row < this.rows; row++) {
                for (let col = 0; col < this.cols; col++) {
                    const hue = (baseHue + row / this.rows * 0.3 + col / this.cols * 0.1) % 1;
                    const id = row * this.cols + col;
                    this.leds[id] = hslToRgb(hue, 0.8, 0.6);
                }
            }

            // Ambient follows base hue
            const ambientColor = hslToRgb(baseHue, 0.7, 0.5);
            for (let i = this.frontLedCount; i < this.totalLeds; i++) {
                this.leds[i] = { ...ambientColor };
            }
            this.updateAmbientGlow(ambientColor);

            if (this.currentPattern === 'rainbow') {
                this.animationId = requestAnimationFrame(animate);
            }
        };

        animate();
    }

    // Stop current pattern
    stopPattern() {
        this.currentPattern = null;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    // Apply bulk LED update
    applyBulkUpdate(ledUpdates) {
        for (const update of ledUpdates) {
            this.setLed(update.id, update.color);
        }
    }

    // Get current state (for API)
    getState() {
        return this.leds.map((led, i) => ({
            id: i,
            color: this.rgbToHex(led.r, led.g, led.b)
        }));
    }

    // Main render loop
    render() {
        const ctx = this.ctx;
        const w = this.displayWidth;
        const h = this.displayHeight;

        // Clear canvas
        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, w, h);

        // If we have a smooth gradient, render it as a single canvas gradient
        // for a beautiful diffused look (like the real frosted lamp)
        if (this.gradientCenter && this.gradientEdge) {
            const cx = w / 2;
            const cy = h / 2;
            const radius = Math.max(w, h) * 0.75;

            const c = this.gradientCenter;
            const e = this.gradientEdge;

            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
            gradient.addColorStop(0, `rgb(${Math.round(c.r)}, ${Math.round(c.g)}, ${Math.round(c.b)})`);
            gradient.addColorStop(0.5, `rgb(${Math.round((c.r + e.r) / 2)}, ${Math.round((c.g + e.g) / 2)}, ${Math.round((c.b + e.b) / 2)})`);
            gradient.addColorStop(1, `rgb(${Math.round(e.r)}, ${Math.round(e.g)}, ${Math.round(e.b)})`);

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, w, h);
        } else {
            // For non-gradient patterns (solid, breathing, wave, rainbow),
            // render individual LEDs with large, overlapping glows for smooth blending
            const cellWidth = w / this.cols;
            const cellHeight = h / this.rows;

            for (let row = 0; row < this.rows; row++) {
                for (let col = 0; col < this.cols; col++) {
                    const id = row * this.cols + col;
                    const led = this.leds[id];
                    const cx = col * cellWidth + cellWidth / 2;
                    const cy = row * cellHeight + cellHeight / 2;

                    const r = Math.round(led.r);
                    const g = Math.round(led.g);
                    const b = Math.round(led.b);

                    // Large glow radius for smooth blending between LEDs
                    const glowRadius = Math.max(cellWidth, cellHeight) * 1.4;

                    const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowRadius);
                    gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 1)`);
                    gradient.addColorStop(0.4, `rgba(${r}, ${g}, ${b}, 0.7)`);
                    gradient.addColorStop(0.7, `rgba(${r}, ${g}, ${b}, 0.3)`);
                    gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

                    ctx.fillStyle = gradient;
                    ctx.fillRect(
                        cx - glowRadius, cy - glowRadius,
                        glowRadius * 2, glowRadius * 2
                    );
                }
            }
        }

        requestAnimationFrame(() => this.render());
    }
}

// HSL to hex conversion
function hslToHex(h, s, l) {
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
        r = hue2rgb(p, q, h / 360 + 1/3);
        g = hue2rgb(p, q, h / 360);
        b = hue2rgb(p, q, h / 360 - 1/3);
    }
    const toHex = x => {
        const hex = Math.round(Math.max(0, Math.min(255, x * 255))).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    return '#' + toHex(r) + toHex(g) + toHex(b);
}

// Knob controller - drag to rotate, maps rotation to a 0-1 value
class KnobController {
    constructor(element, initialValue, onChange) {
        this.el = element;
        this.value = initialValue;
        this.onChange = onChange;
        this.dragging = false;
        this.lastY = 0;

        this.updateVisual();

        this.el.addEventListener('mousedown', (e) => this.onStart(e));
        this.el.addEventListener('touchstart', (e) => this.onStart(e), { passive: false });
        document.addEventListener('mousemove', (e) => this.onMove(e));
        document.addEventListener('touchmove', (e) => this.onMove(e), { passive: false });
        document.addEventListener('mouseup', () => this.onEnd());
        document.addEventListener('touchend', () => this.onEnd());
    }

    onStart(e) {
        e.preventDefault();
        this.dragging = true;
        this.lastY = e.touches ? e.touches[0].clientY : e.clientY;
    }

    onMove(e) {
        if (!this.dragging) return;
        e.preventDefault();
        const y = e.touches ? e.touches[0].clientY : e.clientY;
        const delta = (this.lastY - y) * 0.005;
        this.lastY = y;

        this.value = Math.max(0, Math.min(1, this.value + delta));
        this.updateVisual();
        this.onChange(this.value);
    }

    onEnd() {
        this.dragging = false;
    }

    updateVisual() {
        // Map 0-1 to -150deg to 150deg rotation
        const angle = -150 + this.value * 300;
        this.el.style.transform = `rotate(${angle}deg)`;
    }
}

// Initialize emulator and knobs when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.lamp = new LampEmulator('ledCanvas', 'ambientGlow');

    // Knob state - HSL values for gradient colors
    // Center: warm peach/salmon (hue ~16, sat 52%, light 64%)
    // Edge: warm cream (hue ~35, sat 100%, light 93%)
    let centerHue = 16;
    let edgeHue = 35;
    let brightness = 1.0;

    function updateGradient() {
        const centerHex = hslToHex(centerHue, 0.50, 0.64 * brightness);
        const edgeHex = hslToHex(edgeHue, 0.60, Math.min(0.96, 0.93 * brightness));
        window.lamp.setRadialGradient(centerHex, edgeHex);
    }

    // Left knob: center color hue (warm range 0-60)
    new KnobController(
        document.getElementById('knobCenter'),
        centerHue / 60,
        (val) => {
            centerHue = val * 60;
            updateGradient();
        }
    );

    // Middle knob: edge color hue (warm range 10-70)
    new KnobController(
        document.getElementById('knobEdge'),
        (edgeHue - 10) / 60,
        (val) => {
            edgeHue = 10 + val * 60;
            updateGradient();
        }
    );

    // Right knob: brightness (0.4 - 1.0)
    new KnobController(
        document.getElementById('knobBrightness'),
        (brightness - 0.4) / 0.6,
        (val) => {
            brightness = 0.4 + val * 0.6;
            updateGradient();
        }
    );
});

// Export for use by websocket client
window.LampEmulator = LampEmulator;

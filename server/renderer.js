/**
 * GridRenderer - Converts render commands to bulk LED arrays
 *
 * The LLM outputs high-level drawing elements (text, pixel, rect, line, fill).
 * This renderer converts them into {type: "bulk", leds: [{id, color}, ...]}
 * that the existing LED controller understands.
 *
 * Grid: 10 columns × 14 rows. LED ID = row * 10 + col.
 * Row 0 = top, row 13 = bottom. Col 0 = left, col 9 = right.
 */

// 3×5 pixel font — each glyph is 5 rows of 3-wide bitmaps
// 1 = lit, 0 = dark. Variable width for special chars.
const FONT = {
    '0': [[1,1,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
    '1': [[0,1,0],[1,1,0],[0,1,0],[0,1,0],[1,1,1]],
    '2': [[1,1,1],[0,0,1],[1,1,1],[1,0,0],[1,1,1]],
    '3': [[1,1,1],[0,0,1],[1,1,1],[0,0,1],[1,1,1]],
    '4': [[1,0,1],[1,0,1],[1,1,1],[0,0,1],[0,0,1]],
    '5': [[1,1,1],[1,0,0],[1,1,1],[0,0,1],[1,1,1]],
    '6': [[1,1,1],[1,0,0],[1,1,1],[1,0,1],[1,1,1]],
    '7': [[1,1,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]],
    '8': [[1,1,1],[1,0,1],[1,1,1],[1,0,1],[1,1,1]],
    '9': [[1,1,1],[1,0,1],[1,1,1],[0,0,1],[1,1,1]],
    ':': [[0],[1],[0],[1],[0]],
    '.': [[0],[0],[0],[0],[1]],
    '!': [[1],[1],[1],[0],[1]],
    ' ': [[0,0],[0,0],[0,0],[0,0],[0,0]],
    '-': [[0,0,0],[0,0,0],[1,1,1],[0,0,0],[0,0,0]],
    '+': [[0,0,0],[0,1,0],[1,1,1],[0,1,0],[0,0,0]],
    'A': [[0,1,0],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
    'B': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,1,0]],
    'C': [[1,1,1],[1,0,0],[1,0,0],[1,0,0],[1,1,1]],
    'D': [[1,1,0],[1,0,1],[1,0,1],[1,0,1],[1,1,0]],
    'E': [[1,1,1],[1,0,0],[1,1,1],[1,0,0],[1,1,1]],
    'F': [[1,1,1],[1,0,0],[1,1,1],[1,0,0],[1,0,0]],
    'G': [[1,1,1],[1,0,0],[1,0,1],[1,0,1],[1,1,1]],
    'H': [[1,0,1],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
    'I': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[1,1,1]],
    'J': [[1,1,1],[0,0,1],[0,0,1],[1,0,1],[1,1,1]],
    'K': [[1,0,1],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
    'L': [[1,0,0],[1,0,0],[1,0,0],[1,0,0],[1,1,1]],
    'M': [[1,0,1],[1,1,1],[1,1,1],[1,0,1],[1,0,1]],
    'N': [[1,0,1],[1,1,1],[1,1,1],[1,1,1],[1,0,1]],
    'O': [[1,1,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
    'P': [[1,1,1],[1,0,1],[1,1,1],[1,0,0],[1,0,0]],
    'Q': [[1,1,1],[1,0,1],[1,0,1],[1,1,1],[0,0,1]],
    'R': [[1,1,1],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
    'S': [[1,1,1],[1,0,0],[1,1,1],[0,0,1],[1,1,1]],
    'T': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[0,1,0]],
    'U': [[1,0,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
    'V': [[1,0,1],[1,0,1],[1,0,1],[1,0,1],[0,1,0]],
    'W': [[1,0,1],[1,0,1],[1,1,1],[1,1,1],[1,0,1]],
    'X': [[1,0,1],[1,0,1],[0,1,0],[1,0,1],[1,0,1]],
    'Y': [[1,0,1],[1,0,1],[1,1,1],[0,1,0],[0,1,0]],
    'Z': [[1,1,1],[0,0,1],[0,1,0],[1,0,0],[1,1,1]],
};

const GRID_COLS = 10;
const GRID_ROWS = 14;
const FRONT_LEDS = GRID_COLS * GRID_ROWS; // 140

export class GridRenderer {
    /**
     * Render a list of elements into a bulk LED command.
     * Elements are drawn in order (painter's algorithm — later elements draw over earlier ones).
     *
     * @param {Array} elements - Array of render elements
     * @returns {{ type: string, leds: Array<{id: number, color: string}> }}
     */
    render(elements) {
        // Initialize pixel buffer — null means "not set"
        const buffer = new Array(FRONT_LEDS).fill(null);

        for (const el of elements) {
            switch (el.type) {
                case 'fill':
                    this.drawFill(buffer, el.color || '#000000');
                    break;
                case 'text':
                    this.drawText(buffer, el.content || '', el.x || 0, el.y || 0, el.color || '#FFFFFF');
                    break;
                case 'pixel':
                    this.drawPixel(buffer, el.x, el.y, el.color || '#FFFFFF');
                    break;
                case 'rect':
                    this.drawRect(buffer, el.x || 0, el.y || 0, el.w || 1, el.h || 1, el.color || '#FFFFFF');
                    break;
                case 'line':
                    this.drawLine(buffer, el.x1 || 0, el.y1 || 0, el.x2 || 0, el.y2 || 0, el.color || '#FFFFFF');
                    break;
                case 'circle':
                    this.drawCircle(buffer, el.cx || 5, el.cy || 7, el.r || 3, el.color || '#FFFFFF', el.fill !== false);
                    break;
                case 'triangle':
                    this.drawTriangle(buffer, el.cx || 5, el.cy || 5, el.size || 4, el.direction || 'up', el.color || '#FFFFFF', el.fill !== false);
                    break;
                case 'star':
                    this.drawStar(buffer, el.cx || 5, el.cy || 5, el.r || 3, el.color || '#FFFFFF');
                    break;
                case 'diamond':
                    this.drawDiamond(buffer, el.cx || 5, el.cy || 5, el.r || 3, el.color || '#FFFFFF', el.fill !== false);
                    break;
                case 'heart':
                    this.drawHeart(buffer, el.cx || 5, el.cy || 5, el.size || 4, el.color || '#FFFFFF');
                    break;
                default:
                    // Unknown element type — skip
                    break;
            }
        }

        // Convert buffer to bulk LED array
        const leds = [];
        for (let i = 0; i < FRONT_LEDS; i++) {
            if (buffer[i] !== null) {
                leds.push({ id: i, color: buffer[i] });
            }
        }

        return { type: 'bulk', leds };
    }

    /**
     * Fill all front LEDs with a single color
     */
    drawFill(buffer, color) {
        for (let i = 0; i < FRONT_LEDS; i++) {
            buffer[i] = color;
        }
    }

    /**
     * Draw text string at (x, y) using the built-in 3×5 font.
     * Characters are placed left-to-right with 1px gap between them.
     * Characters that fall outside the grid are clipped.
     */
    drawText(buffer, text, startX, startY, color) {
        let cursorX = startX;
        const upper = text.toUpperCase();

        for (const char of upper) {
            const glyph = FONT[char];
            if (!glyph) {
                // Unknown char — skip with 2px advance
                cursorX += 2;
                continue;
            }

            const charWidth = glyph[0].length;

            // Draw glyph pixels
            for (let row = 0; row < glyph.length; row++) {
                for (let col = 0; col < charWidth; col++) {
                    if (glyph[row][col]) {
                        this.drawPixel(buffer, cursorX + col, startY + row, color);
                    }
                }
            }

            // Advance cursor: character width + 1px gap
            cursorX += charWidth + 1;
        }
    }

    /**
     * Set a single pixel at (x, y)
     */
    drawPixel(buffer, x, y, color) {
        if (x < 0 || x >= GRID_COLS || y < 0 || y >= GRID_ROWS) return;
        const id = Math.floor(y) * GRID_COLS + Math.floor(x);
        if (id >= 0 && id < FRONT_LEDS) {
            buffer[id] = color;
        }
    }

    /**
     * Draw a filled rectangle at (x, y) with dimensions (w, h)
     */
    drawRect(buffer, x, y, w, h, color) {
        for (let row = y; row < y + h; row++) {
            for (let col = x; col < x + w; col++) {
                this.drawPixel(buffer, col, row, color);
            }
        }
    }

    /**
     * Draw a line from (x1, y1) to (x2, y2).
     * Supports horizontal, vertical, and diagonal lines (Bresenham's).
     */
    drawLine(buffer, x1, y1, x2, y2, color) {
        const dx = Math.abs(x2 - x1);
        const dy = Math.abs(y2 - y1);
        const sx = x1 < x2 ? 1 : -1;
        const sy = y1 < y2 ? 1 : -1;
        let err = dx - dy;
        let x = x1, y = y1;

        while (true) {
            this.drawPixel(buffer, x, y, color);
            if (x === x2 && y === y2) break;
            const e2 = 2 * err;
            if (e2 > -dy) { err -= dy; x += sx; }
            if (e2 < dx) { err += dx; y += sy; }
        }
    }
    /**
     * Draw a circle centered at (cx, cy) with radius r.
     * If fill=true, fills the circle. Otherwise draws outline only.
     */
    drawCircle(buffer, cx, cy, r, color, fill = true) {
        for (let y = Math.floor(cy - r); y <= Math.ceil(cy + r); y++) {
            for (let x = Math.floor(cx - r); x <= Math.ceil(cx + r); x++) {
                const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
                if (fill) {
                    if (dist <= r + 0.5) this.drawPixel(buffer, x, y, color);
                } else {
                    if (dist >= r - 0.5 && dist <= r + 0.5) this.drawPixel(buffer, x, y, color);
                }
            }
        }
    }

    /**
     * Draw a triangle centered at (cx, cy) with given size.
     * direction: 'up', 'down', 'left', 'right'
     * If fill=true, fills the triangle. Otherwise draws outline only.
     */
    drawTriangle(buffer, cx, cy, size, direction = 'up', color, fill = true) {
        const half = Math.floor(size / 2);
        if (direction === 'up') {
            for (let row = 0; row <= size; row++) {
                const width = Math.floor(row * half / size);
                const y = cy - half + row;
                if (fill) {
                    for (let dx = -width; dx <= width; dx++) this.drawPixel(buffer, cx + dx, y, color);
                } else {
                    this.drawPixel(buffer, cx - width, y, color);
                    this.drawPixel(buffer, cx + width, y, color);
                    if (row === size) for (let dx = -width; dx <= width; dx++) this.drawPixel(buffer, cx + dx, y, color);
                }
            }
        } else if (direction === 'down') {
            for (let row = 0; row <= size; row++) {
                const width = Math.floor((size - row) * half / size);
                const y = cy - half + row;
                if (fill) {
                    for (let dx = -width; dx <= width; dx++) this.drawPixel(buffer, cx + dx, y, color);
                } else {
                    this.drawPixel(buffer, cx - width, y, color);
                    this.drawPixel(buffer, cx + width, y, color);
                    if (row === 0) for (let dx = -width; dx <= width; dx++) this.drawPixel(buffer, cx + dx, y, color);
                }
            }
        } else if (direction === 'left') {
            for (let col = 0; col <= size; col++) {
                const height = Math.floor(col * half / size);
                const x = cx - half + col;
                if (fill) {
                    for (let dy = -height; dy <= height; dy++) this.drawPixel(buffer, x, cy + dy, color);
                } else {
                    this.drawPixel(buffer, x, cy - height, color);
                    this.drawPixel(buffer, x, cy + height, color);
                }
            }
        } else if (direction === 'right') {
            for (let col = 0; col <= size; col++) {
                const height = Math.floor((size - col) * half / size);
                const x = cx - half + col;
                if (fill) {
                    for (let dy = -height; dy <= height; dy++) this.drawPixel(buffer, x, cy + dy, color);
                } else {
                    this.drawPixel(buffer, x, cy - height, color);
                    this.drawPixel(buffer, x, cy + height, color);
                }
            }
        }
    }

    /**
     * Draw a 5-pointed star centered at (cx, cy) with radius r.
     * Uses a fixed pixel pattern scaled to the radius.
     */
    drawStar(buffer, cx, cy, r, color) {
        // Top point
        this.drawPixel(buffer, cx, cy - r, color);
        // Upper arms
        for (let i = 1; i <= Math.floor(r * 0.4); i++) {
            this.drawPixel(buffer, cx - i, cy - r + i, color);
            this.drawPixel(buffer, cx + i, cy - r + i, color);
        }
        // Middle wide row
        const midY = cy - Math.floor(r * 0.3);
        for (let x = cx - r; x <= cx + r; x++) this.drawPixel(buffer, x, midY, color);
        // Inner body
        for (let i = 0; i <= Math.floor(r * 0.5); i++) {
            const width = Math.floor(r * 0.6) - Math.floor(i * 0.4);
            const y = midY + 1 + i;
            for (let dx = -width; dx <= width; dx++) this.drawPixel(buffer, cx + dx, y, color);
        }
        // Lower V legs
        for (let i = 1; i <= Math.floor(r * 0.8); i++) {
            const y = cy + Math.floor(r * 0.3) + i;
            this.drawPixel(buffer, cx - Math.floor(r * 0.5) - Math.floor(i * 0.3), y, color);
            this.drawPixel(buffer, cx + Math.floor(r * 0.5) + Math.floor(i * 0.3), y, color);
            this.drawPixel(buffer, cx - Math.floor(i * 0.3), y, color);
            this.drawPixel(buffer, cx + Math.floor(i * 0.3), y, color);
        }
        // Bottom point
        this.drawPixel(buffer, cx, cy + r, color);
    }

    /**
     * Draw a diamond centered at (cx, cy) with radius r.
     */
    drawDiamond(buffer, cx, cy, r, color, fill = true) {
        for (let dy = -r; dy <= r; dy++) {
            const width = r - Math.abs(dy);
            if (fill) {
                for (let dx = -width; dx <= width; dx++) this.drawPixel(buffer, cx + dx, cy + dy, color);
            } else {
                this.drawPixel(buffer, cx - width, cy + dy, color);
                this.drawPixel(buffer, cx + width, cy + dy, color);
            }
        }
    }

    /**
     * Draw a heart centered at (cx, cy) with given size.
     */
    drawHeart(buffer, cx, cy, size, color) {
        const r = Math.max(1, Math.floor(size / 3));
        // Two circles for the top bumps
        this.drawCircle(buffer, cx - r, cy - Math.floor(r * 0.5), r, color, true);
        this.drawCircle(buffer, cx + r, cy - Math.floor(r * 0.5), r, color, true);
        // Triangle for the bottom point
        this.drawTriangle(buffer, cx, cy + r, size, 'down', color, true);
    }
}

export default GridRenderer;

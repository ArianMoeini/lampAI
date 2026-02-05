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
}

export default GridRenderer;

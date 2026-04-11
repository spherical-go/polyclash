/**
 * LightRules — client-side rules engine for PolyClash.
 *
 * Provides instant feedback (legal-move highlighting, suicide detection)
 * without waiting for server round-trips. The server remains authoritative;
 * this module only offers a best-effort preview (it does NOT check superko).
 *
 * Board representation mirrors the Python Board class:
 *   - 302-element array, values: 0 = empty, 1 = black, -1 = white
 *   - neighbors: adjacency list keyed by point index
 */

class LightRules {
    /**
     * @param {Object} neighbors  Adjacency map: point index (string key) → array of neighbor indices.
     *                            Converted internally to Map<number, number[]>.
     */
    constructor(neighbors) {
        this.neighbors = new Map();
        for (const [key, value] of Object.entries(neighbors)) {
            this.neighbors.set(Number(key), value.map(Number));
        }
        // Board state: defensive copy kept via setState()
        this.board = new Array(302).fill(0);
    }

    /**
     * Set the current board state.
     * @param {number[]} boardArray  Array of 302 elements (0 = empty, 1 = black, -1 = white).
     */
    setState(boardArray) {
        this.board = boardArray.slice();
    }

    /**
     * Recursive flood-fill liberty check, mirroring Python Board.has_liberty.
     *
     * @param {number}      point   Index of the stone to start from.
     * @param {number|null} color   Color of the group (1 or -1). Defaults to board value at point.
     * @param {Set<number>|null} visited  Set of already-visited points (used by recursion).
     * @returns {boolean} True if the group containing `point` has at least one liberty.
     */
    hasLiberty(point, color, visited) {
        if (color == null) {
            color = this.board[point];
        }
        if (visited == null) {
            visited = new Set();
        }

        if (visited.has(point)) {
            return false;
        }
        visited.add(point);

        var adj = this.neighbors.get(point);
        if (!adj) {
            return false;
        }

        for (var i = 0; i < adj.length; i++) {
            var neighbor = adj[i];
            if (this.board[neighbor] === 0) {
                // Empty neighbor ⇒ liberty exists
                return true;
            }
            if (this.board[neighbor] === color && this.hasLiberty(neighbor, color, visited)) {
                // Same-color neighbor whose group has a liberty
                return true;
            }
        }

        return false;
    }

    /**
     * Return all points belonging to the group that contains `point`.
     *
     * @param {number} point  Index of a stone on the board.
     * @returns {number[]}    Array of point indices in the group (empty if point is unoccupied).
     */
    getGroup(point) {
        var color = this.board[point];
        if (color === 0) {
            return [];
        }

        var group = [];
        var visited = new Set();
        var stack = [point];

        while (stack.length > 0) {
            var current = stack.pop();
            if (visited.has(current)) {
                continue;
            }
            visited.add(current);
            group.push(current);

            var adj = this.neighbors.get(current);
            if (!adj) {
                continue;
            }
            for (var i = 0; i < adj.length; i++) {
                var neighbor = adj[i];
                if (!visited.has(neighbor) && this.board[neighbor] === color) {
                    stack.push(neighbor);
                }
            }
        }

        return group;
    }

    /**
     * Check whether placing a stone at `point` for `player` would capture
     * at least one opponent group.
     *
     * The check is performed on a temporary board so this.board is never mutated.
     *
     * @param {number} point   Index where the stone would be placed.
     * @param {number} player  1 (black) or -1 (white).
     * @returns {boolean}
     */
    wouldCapture(point, player) {
        var opponent = -player;
        var adj = this.neighbors.get(point);
        if (!adj) {
            return false;
        }

        // Temporarily place the stone to evaluate liberties accurately
        this.board[point] = player;

        var captures = false;
        for (var i = 0; i < adj.length; i++) {
            var neighbor = adj[i];
            if (this.board[neighbor] === opponent) {
                if (!this.hasLiberty(neighbor, opponent, null)) {
                    captures = true;
                    break;
                }
            }
        }

        // Restore the board
        this.board[point] = 0;
        return captures;
    }

    /**
     * Determine whether a move at `point` by `player` is likely legal.
     *
     * Rules checked (matching Python Board.play):
     *   1. Point must be empty.
     *   2. After placement the stone must have a liberty, OR the move must
     *      capture at least one opponent group (otherwise it is suicide).
     *
     * Superko is NOT checked — the server is authoritative for that.
     *
     * @param {number} point   Board index (0–301).
     * @param {number} player  1 (black) or -1 (white).
     * @returns {{ legal: boolean, reason: string }}
     */
    checkMove(point, player) {
        if (point < 0 || point >= 302) {
            return { legal: false, reason: "out of bounds" };
        }

        if (this.board[point] !== 0) {
            return { legal: false, reason: "occupied" };
        }

        // Would the move capture any opponent stones?
        var captures = this.wouldCapture(point, player);

        if (captures) {
            // Capturing moves are always legal (suicide is impossible when
            // opponent stones are removed first).
            return { legal: true, reason: "capture" };
        }

        // Temporarily place the stone and check own liberties
        this.board[point] = player;
        var hasLib = this.hasLiberty(point, player, null);
        this.board[point] = 0;

        if (!hasLib) {
            return { legal: false, reason: "suicide" };
        }

        return { legal: true, reason: "ok" };
    }

    /**
     * Return an array of all likely-legal move indices for `player`.
     *
     * @param {number} player  1 (black) or -1 (white).
     * @returns {number[]}
     */
    getLegalMoves(player) {
        var moves = [];
        for (var i = 0; i < 302; i++) {
            if (this.board[i] !== 0) {
                continue;
            }
            var result = this.checkMove(i, player);
            if (result.legal) {
                moves.push(i);
            }
        }
        return moves;
    }
}

window.LightRules = LightRules;

# Client Implementation

This document provides details about the implementation of the PolyClash web client, including the 3D renderer, game logic, network communication, and internationalization.

## Overview

The PolyClash client is a browser-based web application served by the Flask server. It uses Three.js for 3D visualization of the spherical game board and communicates with the server via REST API (fetch POST) and Socket.IO for real-time events.

## File Structure

```
web/
├── index.html          — Game page: canvas, score panel, turn indicator, controls, view map, language selector
├── lobby.html          — Team mode lobby: login/register forms, room list, admin panel
├── css/
│   ├── style.css       — Dark theme (--bg-primary: #1a1a2e), fixed canvas, overlay panels
│   └── lobby.css       — Lobby-specific styles
├── js/
│   ├── main.js         — DOMContentLoaded entry point, wires components, binds buttons
│   ├── board-renderer.js — BoardRenderer class: Three.js scene, geometry, stones, camera views
│   ├── game-client.js  — GameClient class: server communication, game state management
│   ├── light-rules.js  — LightRules class: client-side legality checking
│   ├── i18n.js         — i18n object: 5 languages, browser detection
│   └── lobby.js        — Lobby auth, room list, game creation/joining, admin panel
├── vendor/
│   ├── three.min.js    — Three.js library
│   ├── socket.io.min.js — Socket.IO client library
│   └── OrbitControls.js — Three.js orbit controls
└── data/
    └── board.json      — Board geometry (cities, neighbors, triangles, pentagons, axis, encoder)
```

## Main Components

### Entry Point (main.js)

The `main.js` script runs on `DOMContentLoaded` and orchestrates all components:

1. Auto-detects browser language via `i18n.detectLang()`
2. Initializes `BoardRenderer` with the canvas element and loads board geometry
3. Initializes `LightRules` with neighbor data from the board
4. Initializes `GameClient` with the renderer and rules
5. Wires the stone click handler from renderer to client
6. Binds UI buttons (Pass, Resign, Save Record, Reset)
7. Populates the view map with 8 camera-view buttons (i18n labels)
8. Wires the language selector to update all labels on change
9. Starts the render loop (`renderer.animate()`)
10. Auto-starts the game from URL parameters

```javascript
document.addEventListener('DOMContentLoaded', async function () {
    i18n.detectLang();

    var renderer = new BoardRenderer(canvas);
    await renderer.loadData();

    var rules = new LightRules(renderer.boardData.neighbors);
    var client = new GameClient(renderer, rules);

    renderer.onStoneClick = function (index) {
        client.playMove(index);
    };

    // ... bind buttons, populate view map, start animation ...

    // Auto-start from URL parameters
    var params = new URLSearchParams(window.location.search);
    var urlKey = params.get('key');
    if (urlKey) {
        client.joinWithKey(serverUrl, urlKey, urlAI);
    } else if (window._serverToken) {
        client.startLocalGame(serverUrl, urlSide);
    }
});
```

### 3D Board Renderer (board-renderer.js)

The `BoardRenderer` class manages the Three.js scene and renders the game board:

- Loads board geometry from `/web/data/board.json` (cities, neighbors, triangles, pentagons, axis data)
- Builds the board mesh with vertex colors: 4 continent colors + ocean color
- Creates 302 stone marker spheres (small gray spheres at each city position)
- Handles stone picking via raycaster on `pointerdown`
- Shows hover ring on empty positions when the mouse moves over them
- Marks the last move with a red ring
- Provides 8 preset camera views (4 continents + 4 oceans) with smooth tweened transitions
- Uses `OrbitControls` for free camera rotation with damping

```javascript
function BoardRenderer(canvas) {
    // WebGL renderer, scene, camera, lights, orbit controls
    // Raycaster for stone picking
    // Hover ring and last-move marker management
}

BoardRenderer.prototype.loadData = function () { /* fetch /web/data/board.json */ };
BoardRenderer.prototype.buildBoard = function () { /* construct mesh, edges, stone markers */ };
BoardRenderer.prototype.setStone = function (index, color) { /* 0=empty, 1=black, -1=white */ };
BoardRenderer.prototype.changeView = function (index) { /* smooth camera tween to axis[index] */ };
BoardRenderer.prototype.markLastMove = function (index) { /* red ring on last played stone */ };
BoardRenderer.prototype.animate = function () { /* requestAnimationFrame render loop */ };
```

### Game Client (game-client.js)

The `GameClient` class manages server communication and game state:

**State:**
- `boardState` — 302-element array (0=empty, 1=black, -1=white)
- `currentPlayer` — 1 (black) or -1 (white)
- `score` — `{ black, white, unclaimed }` (fractions)
- `counter` — move counter
- `mode` — `'local'` or `'network'`
- `aiMode` — when true, auto-plays via `/sphgo/genmove`
- `side` — this player's color (1 or -1)

**Key methods:**

```javascript
class GameClient {
    async startLocalGame(serverUrl, side)    // Solo mode: create game, join both sides, ready, AI first if white
    async joinWithKey(serverUrl, key, aiMode) // Family/team: whoami → join → socket → ready → fetchState
    async playMove(point)                     // Client-side check → POST /sphgo/play → fetchState → AI if local
    async requestAIMove()                     // POST /sphgo/genmove with AI token
    async fetchState()                        // POST /sphgo/state → updateBoardState
    async pass()                              // Increment counter, fetchState
    async resign()                            // POST /sphgo/resign
    async resetGame()                         // POST /sphgo/close, disconnect socket, clear state
    async downloadRecord()                    // POST /sphgo/record → download JSON
    connectSocket(serverUrl)                  // Socket.IO: join, ready, start, played, passed, game_over
    autoPlayIfAI()                            // If aiMode and our turn, trigger _doAIMove after delay
    updateUI()                                // Update score panel, turn indicator, move counter
}
```

**Server communication:** All API calls use `fetch POST` to `/sphgo/*` endpoints with JSON body containing `token` (or `key`). Socket.IO is used only in network/family mode for real-time events.

### Light Rules (light-rules.js)

The `LightRules` class provides instant client-side feedback without server round-trips:

- Maintains a copy of the 302-element board state
- Uses the neighbor adjacency map from board data
- `hasLiberty(point, color, visited)` — recursive flood-fill liberty check
- `getGroup(point)` — returns all points in a connected group
- `wouldCapture(point, player)` — checks if placing a stone would capture opponent groups
- `checkMove(point, player)` — returns `{ legal, reason }` checking occupancy, suicide, capture
- `getLegalMoves(player)` — returns array of all likely-legal move indices

**Important:** The light rules do NOT check superko. The server is authoritative for all rules; this module only provides best-effort preview for UI responsiveness.

### Internationalization (i18n.js)

The `i18n` object supports 5 languages:

| Code | Language |
|------|----------|
| `en` | English |
| `zh-Hans` | 简体中文 (Simplified Chinese) |
| `zh-Hant` | 繁體中文 (Traditional Chinese) |
| `ja` | 日本語 (Japanese) |
| `ko` | 한국어 (Korean) |

**API:**
- `i18n.detectLang()` — auto-detect from `navigator.language`, mapping Chinese region variants to script variants
- `i18n.setLang(lang)` / `i18n.getLang()` — set/get current language
- `i18n.t(key)` — translate a key, falling back to English

Translation keys cover: game title, 8 view names (4 continents + 4 oceans), score labels, turn indicators, status messages, and button labels.

### Lobby (lobby.js)

The lobby is used in team mode and provides:

**Auth:**
- Login via `POST /sphgo/auth/login` with username/password
- Registration via `POST /sphgo/auth/register` with username/password/invite code
- Logout via `POST /sphgo/auth/logout`
- Session persistence in `localStorage` with auto-restore on page load

**Room management:**
- Lists active game rooms via `POST /sphgo/lobby`
- Creates new games via `POST /sphgo/lobby/create`
- Joins games via `POST /sphgo/lobby/join` → redirects to `/?key=...`

**Admin panel (visible to admin users):**
- Generate invite codes via `POST /sphgo/auth/invite`
- List all invite codes via `POST /sphgo/auth/invites`

## Game Modes and Flows

### Solo Mode

URL: `/?token=xxx&side=black`

1. `index.html` inline script detects `?token=` and stores it as `window._serverToken`
2. `main.js` detects `window._serverToken` and calls `client.startLocalGame(serverUrl, side)`
3. `startLocalGame()` creates a new game via `/sphgo/new` using the server token
4. Joins as the human's side, joins AI as the other side
5. Marks both players ready
6. If the human plays white, calls `requestAIMove()` so the AI (black) moves first

Typically launched via `polyclash solo --side black`.

### Family Mode

URL: `/?key=xxx` (optionally `&ai=1`)

1. `main.js` detects `?key=` and calls `client.joinWithKey(serverUrl, key, aiMode)`
2. `joinWithKey()` calls `/sphgo/whoami` to discover the role for the key
3. Joins the game with the discovered role via `/sphgo/join`
4. Connects Socket.IO for real-time events (`joined`, `ready`, `start`, `played`, `passed`, `game_over`)
5. Marks the player as ready via `/sphgo/ready`
6. Fetches initial state via `/sphgo/state`
7. If `aiMode` is true, auto-plays via `/sphgo/genmove` when it is this player's turn

Typically launched via `polyclash family`, which prints URLs for black, white, and viewer.

### Team Mode

URL: `/` (no key or token → redirected to lobby)

1. Server detects `POLYCLASH_TEAM_MODE` and redirects to `lobby.html`
2. User logs in or registers (invite code required)
3. Lobby shows a list of active game rooms with join buttons
4. User creates or joins a game → redirected to `/?key=xxx`
5. Game proceeds as in family mode

Typically launched via `polyclash team`.

## User Interaction

### Mouse Interaction

- **Click on a stone position:** Raycaster picks the nearest stone mesh; `onStoneClick` callback forwards the index to `GameClient.playMove()`
- **Hover over empty positions:** A colored ring (black or white, matching current player) appears around the hovered position
- **Orbit controls:** Click and drag to rotate the board freely

### View Map

The view map panel contains 8 buttons, one for each preset camera view:
- 4 continents: Amberland, Jadeland, Goldenland, Amethyst Land
- 4 oceans: Coral Ocean, Pearl Ocean, Sapphire Ocean, Obsidian Ocean

Clicking a button triggers a smooth 600ms camera tween to the corresponding axis position.

### Game Controls

- **Pass:** Skips the current turn
- **Resign:** Forfeits the game
- **Save Record:** Downloads the game record as a JSON file
- **Reset:** Closes the game on the server, disconnects the socket, and resets all local state

## Error Handling

- Invalid moves are caught client-side by `LightRules` before sending to the server
- Server-rejected moves display the error message in the status bar
- Network errors are caught and displayed in the status bar
- Socket.IO errors trigger a status bar message

## Logging

The client logs to the browser console via `console.log` / `console.error`. Status messages are displayed in the `#status-bar` element at the bottom of the game page.

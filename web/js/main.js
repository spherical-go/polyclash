/**
 * PolyClash Web Client – Application entry point
 *
 * Wires together BoardRenderer, LightRules and GameClient,
 * binds UI controls, and starts the render loop.
 */

document.addEventListener('DOMContentLoaded', async function () {
    var canvas = document.getElementById('board-canvas');

    // Initialize renderer
    var renderer = new BoardRenderer(canvas);
    await renderer.loadData();

    // Initialize light rules with neighbor data
    var rules = new LightRules(renderer.boardData.neighbors);

    // Initialize game client
    var client = new GameClient(renderer, rules);

    // Stone click handler – forward to game client
    renderer.onStoneClick = function (index) {
        client.playMove(index);
    };

    // ---- UI button wiring ----

    document.getElementById('btn-new-local').addEventListener('click', function () {
        var serverUrl = document.getElementById('server-url').value;
        var token = prompt('Enter server token:');
        if (token) {
            window._serverToken = token;
            client.startLocalGame(serverUrl);
        }
    });

    document.getElementById('btn-new-network').addEventListener('click', function () {
        var serverUrl = document.getElementById('server-url').value;
        var token = prompt('Enter server token:');
        if (token) {
            window._serverToken = token;
            client.createNetworkGame(serverUrl);
        }
    });

    document.getElementById('btn-join-game').addEventListener('click', function () {
        var serverUrl = document.getElementById('server-url').value;
        var key = document.getElementById('join-game-id').value;
        var role = prompt('Enter role (black/white):');
        if (key && role) {
            client.joinGame(serverUrl, key, role);
        }
    });

    document.getElementById('btn-reset').addEventListener('click', function () {
        client.resetGame();
    });

    // Start animation loop
    renderer.animate();

    console.log('PolyClash Web Client initialized');
});

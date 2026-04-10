/**
 * PolyClash Web Client – Application entry point
 *
 * Wires together BoardRenderer, LightRules and GameClient,
 * binds UI controls, and starts the render loop.
 */

document.addEventListener('DOMContentLoaded', async function () {
    // Auto-detect language
    i18n.detectLang();

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

    // ---- Update all UI labels from i18n ----

    function updateAllLabels() {
        // Page title
        document.title = i18n.t('game_title');

        document.getElementById('btn-new-local').textContent = i18n.t('btn_local');
        document.getElementById('btn-pass').textContent = i18n.t('btn_pass');
        document.getElementById('btn-reset').textContent = i18n.t('btn_reset');
        document.getElementById('btn-save-record').textContent = i18n.t('btn_save');
        document.getElementById('btn-new-network').textContent = i18n.t('btn_network');
        document.getElementById('btn-join-game').textContent = i18n.t('btn_join');
        document.getElementById('status-bar').textContent = i18n.t('status_welcome');
        var serverLabel = document.querySelector('#connection-panel label');
        if (serverLabel) serverLabel.textContent = i18n.t('label_server');
    }

    updateAllLabels();

    // ---- UI button wiring ----

    document.getElementById('btn-new-local').addEventListener('click', function () {
        var serverUrl = document.getElementById('server-url').value;
        var token = prompt(i18n.t('prompt_token'));
        if (token) {
            window._serverToken = token;
            client.startLocalGame(serverUrl);
        }
    });

    document.getElementById('btn-new-network').addEventListener('click', function () {
        var serverUrl = document.getElementById('server-url').value;
        var token = prompt(i18n.t('prompt_token'));
        if (token) {
            window._serverToken = token;
            client.createNetworkGame(serverUrl);
        }
    });

    document.getElementById('btn-join-game').addEventListener('click', function () {
        var serverUrl = document.getElementById('server-url').value;
        var key = document.getElementById('join-game-id').value;
        var role = prompt(i18n.t('prompt_role'));
        if (key && role) {
            client.joinGame(serverUrl, key, role);
        }
    });

    document.getElementById('btn-pass').addEventListener('click', function () {
        client.pass();
    });

    document.getElementById('btn-save-record').addEventListener('click', function () {
        client.downloadRecord();
    });

    document.getElementById('btn-reset').addEventListener('click', function () {
        client.resetGame();
    });

    // View map buttons
    var viewButtons = document.querySelectorAll('.view-btn');
    for (var i = 0; i < viewButtons.length; i++) {
        viewButtons[i].addEventListener('click', function () {
            var viewIndex = parseInt(this.getAttribute('data-view'), 10);
            renderer.changeView(viewIndex);
        });
    }

    // ---- View map with i18n names ----

    function populateViewMap() {
        var grid = document.getElementById('view-map-grid');
        grid.innerHTML = '';
        for (var i = 0; i < 8; i++) {
            var btn = document.createElement('button');
            btn.className = 'view-btn';
            btn.setAttribute('data-view', i);
            btn.textContent = i18n.t('view_' + i);
            btn.addEventListener('click', (function (idx) {
                return function () { renderer.changeView(idx); };
            })(i));
            grid.appendChild(btn);
        }
    }

    populateViewMap();

    // ---- Language selector ----

    var langSelect = document.getElementById('lang-select');
    if (langSelect) {
        langSelect.value = i18n.getLang();
        langSelect.addEventListener('change', function () {
            i18n.setLang(this.value);
            updateAllLabels();
            populateViewMap();
            client.updateUI();
        });
    }

    // Start animation loop
    renderer.animate();

    // Auto-start local game if token was provided via URL (solo mode)
    if (window._serverToken) {
        var statusBar = document.getElementById('status-bar');
        statusBar.textContent = i18n.t('status_starting');
        var serverUrl = document.getElementById('server-url').value;
        setTimeout(function () {
            client.startLocalGame(serverUrl);
        }, 500);
    }

    console.log('PolyClash Web Client initialized');
});

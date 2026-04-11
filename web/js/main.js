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
        document.title = i18n.t('game_title');
        document.getElementById('btn-pass').textContent = i18n.t('btn_pass');
        document.getElementById('btn-resign').textContent = i18n.t('btn_resign');
        document.getElementById('btn-reset').textContent = i18n.t('btn_reset');
        document.getElementById('btn-save-record').textContent = i18n.t('btn_save');
        document.getElementById('status-bar').textContent = i18n.t('status_welcome');
    }

    updateAllLabels();

    // ---- UI button wiring ----

    document.getElementById('btn-pass').addEventListener('click', function () {
        client.pass();
    });

    document.getElementById('btn-resign').addEventListener('click', function () {
        client.resign();
    });

    document.getElementById('btn-save-record').addEventListener('click', function () {
        client.downloadRecord();
    });

    document.getElementById('btn-reset').addEventListener('click', function () {
        client.resetGame();
    });

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

    // ---- Auto-start from URL parameters ----

    var params = new URLSearchParams(window.location.search);
    var urlKey = params.get('key');
    var urlSide = params.get('side') || 'black';

    if (urlKey) {
        // Family / network mode: auto-join with key (role inferred from server)
        var statusBar = document.getElementById('status-bar');
        statusBar.textContent = i18n.t('status_starting');
        var serverUrl = window.location.origin;
        setTimeout(function () {
            client.joinWithKey(serverUrl, urlKey);
        }, 500);
    } else if (window._serverToken) {
        // Solo mode: start local game with chosen side
        var statusBar = document.getElementById('status-bar');
        statusBar.textContent = i18n.t('status_starting');
        var serverUrl = window.location.origin;
        setTimeout(function () {
            client.startLocalGame(serverUrl, urlSide);
        }, 500);
    }

    console.log('PolyClash Web Client initialized');
});

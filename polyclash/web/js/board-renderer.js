// board-renderer.js — Three.js renderer for the PolyClash snub dodecahedron board
// Depends on THREE (global) and THREE.OrbitControls loaded via CDN

(function () {
    "use strict";

    var CONTINENT_COLORS = {
        0: [0.22, 0.24, 0.35], // 玄·水 — 北方寒地，深玄青
        1: [0.88, 0.83, 0.68], // 白·金 — 南方温带，暖白金
        2: [0.25, 0.65, 0.60], // 青·木 — 赤道湿热，苍翠
        3: [0.78, 0.38, 0.28], // 赤·火 — 赤道干热，朱砂
    };
    var OCEAN_COLOR = [0.3, 0.5, 0.7];
    var STONE_EMPTY_COLOR = new THREE.Color(0.5, 0.5, 0.5);
    var STONE_BLACK_COLOR = new THREE.Color(0.0, 0.0, 0.0);
    var STONE_WHITE_COLOR = new THREE.Color(1.0, 1.0, 1.0);
    var STONE_RADIUS = 0.015;
    var STONE_PLACED_SCALE = 2.0;  // placed stones are 2x the empty marker
    var RING_SEGMENTS = 32;

    // Reusable circle geometry (unit circle in XY plane, to be scaled/positioned)
    function createCircleGeometry(radius, segments) {
        var pts = [];
        for (var i = 0; i <= segments; i++) {
            var a = (i / segments) * Math.PI * 2;
            pts.push(new THREE.Vector3(Math.cos(a) * radius, Math.sin(a) * radius, 0));
        }
        var geo = new THREE.BufferGeometry().setFromPoints(pts);
        return geo;
    }

    // Place a LineLoop at a city position, oriented outward from sphere center
    function createRing(position, radius, color) {
        var geo = createCircleGeometry(radius, RING_SEGMENTS);
        var mat = new THREE.LineBasicMaterial({ color: color });
        var ring = new THREE.LineLoop(geo, mat);
        ring.position.set(position[0], position[1], position[2]);
        // Orient ring face outward: lookAt a point further from center
        var outward = new THREE.Vector3(position[0] * 2, position[1] * 2, position[2] * 2);
        ring.lookAt(outward);
        return ring;
    }
    var CAMERA_DISTANCE = 3.5;
    var BG_COLOR = 0x555555;

    function BoardRenderer(canvas) {
        this.canvas = canvas;
        this.boardData = null;
        this.stoneMeshes = [];
        this.onStoneClick = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this._highlightedIndices = [];
        this._hoveredIndex = -1;
        this._hoverRing = null;
        this._currentPlayerColor = 1; // 1 = black, -1 = white
        this._lastMoveMarker = null;

        // Renderer – use window dimensions because canvas CSS is 100% viewport
        var w = window.innerWidth;
        var h = window.innerHeight;
        this.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setClearColor(BG_COLOR);
        this.renderer.setSize(w, h);

        // Scene
        this.scene = new THREE.Scene();

        // Camera
        this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);

        // Lights
        var ambient = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambient);
        var directional = new THREE.DirectionalLight(0xffffff, 0.8);
        directional.position.set(3, 5, 4);
        this.scene.add(directional);

        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.12;

        // Resize
        this._boundResize = this.onResize.bind(this);
        window.addEventListener("resize", this._boundResize);

        // Picking
        this.setupPicking();
    }

    // ── Data loading ────────────────────────────────────────────────────

    BoardRenderer.prototype.loadData = function () {
        var self = this;
        return fetch("/web/data/board.json")
            .then(function (res) { return res.json(); })
            .then(function (data) {
                self.boardData = data;
                self.buildBoard();
                // Set initial camera position from axis[0]
                var ax = data.axis[0];
                self.camera.position.set(
                    ax[0] * CAMERA_DISTANCE,
                    ax[1] * CAMERA_DISTANCE,
                    ax[2] * CAMERA_DISTANCE
                );
                self.camera.lookAt(0, 0, 0);
            });
    };

    // ── Board construction ──────────────────────────────────────────────

    BoardRenderer.prototype.buildBoard = function () {
        var data = this.boardData;
        var cities = data.cities;
        var polysmalls = data.polysmalls;
        var polylarges = data.polylarges;
        var triangles = data.triangles;
        var pentagons = data.pentagons;

        // Precompute per-face colors (polysmalls then polylarges)
        var totalFaces = polysmalls.length + polylarges.length; // 240 + 60 = 300
        var faceColors = new Array(totalFaces);

        // Polysmalls: 3 faces per triangle
        for (var ti = 0; ti < triangles.length; ti++) {
            var tri = triangles[ti];
            var groups = [Math.floor(tri[0] / 15), Math.floor(tri[1] / 15), Math.floor(tri[2] / 15)];
            var sameGroup = (groups[0] === groups[1] && groups[1] === groups[2]);
            var color = sameGroup ? CONTINENT_COLORS[groups[0]] : OCEAN_COLOR;
            for (var j = 0; j < 3; j++) {
                faceColors[ti * 3 + j] = color;
            }
        }

        // Polylarges: 5 faces per pentagon
        for (var pi = 0; pi < pentagons.length; pi++) {
            var pent = pentagons[pi];
            var pgroups = [];
            for (var k = 0; k < pent.length; k++) {
                pgroups.push(Math.floor(pent[k] / 15));
            }
            var allSame = true;
            for (var k = 1; k < pgroups.length; k++) {
                if (pgroups[k] !== pgroups[0]) { allSame = false; break; }
            }
            var pcolor = allSame ? CONTINENT_COLORS[pgroups[0]] : OCEAN_COLOR;
            for (var j = 0; j < 5; j++) {
                faceColors[240 + pi * 5 + j] = pcolor;
            }
        }

        // Build BufferGeometry: each quad -> 2 triangles = 6 vertices
        var allQuads = polysmalls.concat(polylarges);
        var vertCount = allQuads.length * 6;
        var positions = new Float32Array(vertCount * 3);
        var colors = new Float32Array(vertCount * 3);

        for (var fi = 0; fi < allQuads.length; fi++) {
            var quad = allQuads[fi];
            var a = cities[quad[0]];
            var b = cities[quad[1]];
            var c = cities[quad[2]];
            var d = cities[quad[3]];
            var fc = faceColors[fi];
            var base = fi * 6 * 3;

            // Triangle 1: a, b, c
            positions[base]     = a[0]; positions[base + 1]  = a[1]; positions[base + 2]  = a[2];
            positions[base + 3] = b[0]; positions[base + 4]  = b[1]; positions[base + 5]  = b[2];
            positions[base + 6] = c[0]; positions[base + 7]  = c[1]; positions[base + 8]  = c[2];
            // Triangle 2: a, c, d
            positions[base + 9]  = a[0]; positions[base + 10] = a[1]; positions[base + 11] = a[2];
            positions[base + 12] = c[0]; positions[base + 13] = c[1]; positions[base + 14] = c[2];
            positions[base + 15] = d[0]; positions[base + 16] = d[1]; positions[base + 17] = d[2];

            // Colors for all 6 vertices
            for (var v = 0; v < 6; v++) {
                colors[base + v * 3]     = fc[0];
                colors[base + v * 3 + 1] = fc[1];
                colors[base + v * 3 + 2] = fc[2];
            }
        }

        var boardGeo = new THREE.BufferGeometry();
        boardGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        boardGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
        boardGeo.computeVertexNormals();

        var boardMat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
        var boardMesh = new THREE.Mesh(boardGeo, boardMat);
        boardMesh.name = "board";
        this.scene.add(boardMesh);

        // Edges – draw from neighbor adjacency data for completeness
        var neighbors = this.boardData.neighbors;
        var edgePositions = [];
        var visited = {};
        for (var ei = 0; ei < cities.length; ei++) {
            var nbs = neighbors[String(ei)];
            if (!nbs) continue;
            for (var ni = 0; ni < nbs.length; ni++) {
                var nb = nbs[ni];
                var edgeKey = ei < nb ? ei + "_" + nb : nb + "_" + ei;
                if (visited[edgeKey]) continue;
                visited[edgeKey] = true;
                var pa = cities[ei], pb = cities[nb];
                edgePositions.push(pa[0], pa[1], pa[2], pb[0], pb[1], pb[2]);
            }
        }
        var edgesGeo = new THREE.BufferGeometry();
        edgesGeo.setAttribute("position", new THREE.Float32BufferAttribute(edgePositions, 3));
        var edgesMat = new THREE.LineBasicMaterial({ color: 0x000000 });
        var edgesLine = new THREE.LineSegments(edgesGeo, edgesMat);
        edgesLine.name = "boardEdges";
        this.scene.add(edgesLine);

        // Stone markers
        var stoneGeo = new THREE.SphereGeometry(STONE_RADIUS, 12, 8);
        this.stoneMeshes = [];

        for (var i = 0; i < cities.length; i++) {
            var mat = new THREE.MeshLambertMaterial({ color: STONE_EMPTY_COLOR.clone() });
            var sphere = new THREE.Mesh(stoneGeo, mat);
            var p = cities[i];
            sphere.position.set(p[0], p[1], p[2]);
            sphere.userData.stoneIndex = i;
            sphere.name = "stone_" + i;
            this.scene.add(sphere);
            this.stoneMeshes.push(sphere);
        }
    };

    // ── Stone state ─────────────────────────────────────────────────────

    BoardRenderer.prototype.setStone = function (index, color) {
        var mesh = this.stoneMeshes[index];
        if (!mesh) return;
        if (color === 1) {
            mesh.material.color.copy(STONE_BLACK_COLOR);
            mesh.scale.set(STONE_PLACED_SCALE, STONE_PLACED_SCALE, STONE_PLACED_SCALE);
        } else if (color === -1) {
            mesh.material.color.copy(STONE_WHITE_COLOR);
            mesh.scale.set(STONE_PLACED_SCALE, STONE_PLACED_SCALE, STONE_PLACED_SCALE);
        } else {
            mesh.material.color.copy(STONE_EMPTY_COLOR);
            mesh.scale.set(1, 1, 1);
        }
    };

    BoardRenderer.prototype.resetStones = function () {
        for (var i = 0; i < this.stoneMeshes.length; i++) {
            this.setStone(i, 0);
        }
    };

    // ── Highlighting ────────────────────────────────────────────────────

    BoardRenderer.prototype.highlightLegalMoves = function (moves) {
        // intentionally minimal – no visual change to avoid clutter
    };

    BoardRenderer.prototype.clearHighlights = function () {
        // no-op
    };

    // ── Picking ─────────────────────────────────────────────────────────

    BoardRenderer.prototype.setupPicking = function () {
        var self = this;
        this.canvas.addEventListener("pointerdown", function (event) {
            var rect = self.canvas.getBoundingClientRect();
            self.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            self.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            self.raycaster.setFromCamera(self.mouse, self.camera);
            var intersects = self.raycaster.intersectObjects(self.stoneMeshes, false);
            if (intersects.length > 0 && self.onStoneClick) {
                var idx = intersects[0].object.userData.stoneIndex;
                if (idx !== undefined) {
                    self.onStoneClick(idx);
                }
            }
        });

        this.canvas.addEventListener("mousemove", function (event) {
            var rect = self.canvas.getBoundingClientRect();
            self.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            self.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            self.raycaster.setFromCamera(self.mouse, self.camera);
            var intersects = self.raycaster.intersectObjects(self.stoneMeshes, false);

            var newIndex = -1;
            if (intersects.length > 0) {
                var idx = intersects[0].object.userData.stoneIndex;
                if (idx !== undefined) {
                    newIndex = idx;
                }
            }

            if (newIndex !== self._hoveredIndex) {
                // Remove previous hover ring
                if (self._hoverRing) {
                    self.scene.remove(self._hoverRing);
                    self._hoverRing.geometry.dispose();
                    self._hoverRing.material.dispose();
                    self._hoverRing = null;
                }

                // Add hover ring on empty stone
                if (newIndex >= 0) {
                    var mesh = self.stoneMeshes[newIndex];
                    if (mesh && mesh.scale.x !== STONE_PLACED_SCALE) {
                        var hoverColor = self._currentPlayerColor === 1 ? 0x444444 : 0xcccccc;
                        var city = self.boardData.cities[newIndex];
                        self._hoverRing = createRing(city, 0.04, hoverColor);
                        self.scene.add(self._hoverRing);
                    }
                }

                self._hoveredIndex = newIndex;
            }
        });

        this.canvas.addEventListener("mouseleave", function () {
            if (self._hoverRing) {
                self.scene.remove(self._hoverRing);
                self._hoverRing.geometry.dispose();
                self._hoverRing.material.dispose();
                self._hoverRing = null;
            }
            self._hoveredIndex = -1;
        });
    };

    // ── Hover color ────────────────────────────────────────────────────

    BoardRenderer.prototype.setCurrentPlayerColor = function (player) {
        this._currentPlayerColor = player;
    };

    // ── Last move marker ────────────────────────────────────────────────

    BoardRenderer.prototype.markLastMove = function (index) {
        // Remove previous marker
        if (this._lastMoveMarker) {
            this.scene.remove(this._lastMoveMarker);
            this._lastMoveMarker.geometry.dispose();
            this._lastMoveMarker.material.dispose();
            this._lastMoveMarker = null;
        }

        if (!this.boardData || !this.boardData.cities[index]) return;

        var city = this.boardData.cities[index];
        this._lastMoveMarker = createRing(city, 0.038, 0xff4444);
        this._lastMoveMarker.name = "lastMoveMarker";
        this.scene.add(this._lastMoveMarker);
    };

    // ── Camera views ────────────────────────────────────────────────────

    BoardRenderer.prototype.changeView = function (index) {
        if (!this.boardData || !this.boardData.axis[index]) return;
        var ax = this.boardData.axis[index];
        this._tweenCamera(new THREE.Vector3(
            ax[0] * CAMERA_DISTANCE,
            ax[1] * CAMERA_DISTANCE,
            ax[2] * CAMERA_DISTANCE
        ));
    };

    BoardRenderer.prototype.lookAtPoint = function (pointIndex) {
        if (!this.boardData || !this.boardData.cities[pointIndex]) return;
        var city = this.boardData.cities[pointIndex];
        var dir = new THREE.Vector3(city[0], city[1], city[2]).normalize();
        this._tweenCamera(dir.multiplyScalar(CAMERA_DISTANCE));
    };

    BoardRenderer.prototype._tweenCamera = function (target) {
        var self = this;
        var start = self.camera.position.clone();
        var startTime = performance.now();
        var duration = 600;
        function step(now) {
            var t = Math.min((now - startTime) / duration, 1);
            t = t * t * (3 - 2 * t);
            self.camera.position.lerpVectors(start, target, t);
            self.camera.position.normalize().multiplyScalar(CAMERA_DISTANCE);
            self.camera.lookAt(0, 0, 0);
            if (t < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    };

    // ── Animation loop ──────────────────────────────────────────────────

    BoardRenderer.prototype.animate = function () {
        var self = this;
        requestAnimationFrame(function () { self.animate(); });
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    };

    // ── Resize ──────────────────────────────────────────────────────────

    BoardRenderer.prototype.onResize = function () {
        var w = window.innerWidth;
        var h = window.innerHeight;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    };

    window.BoardRenderer = BoardRenderer;
})();

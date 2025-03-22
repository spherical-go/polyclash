# Game Rules

PolyClash is a Go-like game played on a spherical board represented by a snub dodecahedron. This document explains the rules of the game.

## The Board

The PolyClash board is a snub dodecahedron, which is an Archimedean solid with:
- 60 vertices (where stones are placed)
- 92 faces (12 pentagons and 80 triangles)
- 150 edges

The board is visualized in 3D, allowing players to rotate and view it from different angles.

## Basic Concepts

### Stones

- Players take turns placing stones on the vertices of the snub dodecahedron
- Black plays first, followed by White
- Once placed, stones cannot be moved
- Stones can be captured and removed from the board

### Liberties

- A liberty is an empty adjacent vertex connected by an edge
- A stone or group of stones must have at least one liberty to remain on the board
- Stones of the same color that are connected by edges form a group and share liberties

### Territory

- The game board is divided into regions (faces)
- A region is controlled by a player if only their stones surround it
- If both players have stones surrounding a region, control is proportional to the number of stones

## Game Rules

### Placement

1. Players take turns placing stones on empty vertices
2. Black plays first, followed by White
3. A stone cannot be placed on an already occupied vertex

### Capture

1. If a stone or group of stones loses all its liberties (adjacent empty vertices), it is captured and removed from the board
2. Capturing opponent stones can create new liberties for your own stones

### Ko Rule

1. A player cannot make a move that would recreate the board position from their previous move
2. This prevents infinite loops of capturing and recapturing

### Suicide Rule

1. A player cannot place a stone that would immediately have no liberties, unless it captures opponent stones in the process
2. This prevents "suicide" moves

## Scoring

The score is calculated based on the area controlled by each player:

1. Each face (triangle or pentagon) on the board contributes to the score
2. If a face is surrounded only by stones of one color, that player gets the full value of the face
3. If a face is surrounded by stones of both colors, the score is divided proportionally
4. The player with the higher score wins

## Game Modes

### Local Play

1. **Human vs. Human**: Two players take turns using the same computer
2. **Human vs. AI**: Play against the computer AI

### Network Play

1. **Create Game**: Create a new game and invite another player
2. **Join Game**: Join an existing game using a game key
3. **Spectate**: Watch a game without participating

## Game End

The game ends when:

1. Both players pass consecutively
2. One player resigns
3. No legal moves remain

## Strategy Tips

1. **Control the Center**: The center regions provide more connections and strategic options
2. **Build Connections**: Connected stones are stronger and harder to capture
3. **Create Eyes**: Formations with internal liberties (eyes) are harder to capture
4. **Balance Territory and Influence**: Balance between securing territory and maintaining influence over the board

## Differences from Traditional Go

1. **Spherical Board**: The board has no edges, changing the strategic landscape
2. **Vertex Placement**: Stones are placed on vertices rather than intersections
3. **Scoring System**: Scoring is based on faces rather than enclosed areas
4. **Board Size**: The board has 60 vertices, compared to the 19×19 (361 intersections) of a standard Go board

## User Interface

The game interface provides several tools to help you play:

1. **3D View**: Rotate and zoom the board to see all angles
2. **Overlay Map**: Quick access to different viewpoints
3. **Score Display**: Real-time score tracking
4. **Turn Indicator**: Shows whose turn it is

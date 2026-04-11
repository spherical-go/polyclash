# PolyClash Overview

## Introduction

PolyClash is a Go-like board game played on a spherical surface represented by a snub dodecahedron. The game combines the strategic depth of Go with the unique geometry of a spherical board, creating a novel gaming experience.

Like mathematical truth, Go is an eternal game in the universe. Similarly, the snub dodecahedron is also an eternal geometric shape, which is the Archimedean polyhedron with the most sphericity. PolyClash combines these two to create a new game with simple rules that make for interesting gameplay.

## Key Features

- **3D Spherical Board**: Play on a snub dodecahedron, providing a unique spherical Go experience
- **Multiple Game Modes**: Solo (vs AI), family (LAN), team (self-hosted with accounts), or deploy a dedicated server
- **3D Visualization**: Fully interactive 3D visualization of the game board using Three.js in the browser
- **AI Opponent**: Built-in AI that uses strategic algorithms to provide a challenging opponent
- **Network Play**: Play against other players over a local network or the internet
- **Team Mode**: Self-hosted server with user accounts (SQLite), invite codes, lobby, and configurable room limits
- **Board Persistence**: Save and restore game state via `to_dict`/`from_dict` and `save_board`/`load_board`
- **Internationalization**: UI available in 5 languages — English, 简体中文, 繁體中文, 日本語, 한국어
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Technical Overview

PolyClash is built using Python with the following key technologies:

- **Flask**: Web server and REST API
- **Socket.IO**: Real-time communication between server and clients
- **Three.js**: 3D visualization of the game board in the browser
- **SQLite**: User account storage for team mode
- **Redis**: Optional backend for data storage in production environments

## Project Structure

The project is organized into several key components:

- **Web Client**: A browser-based interface (`web/`) using Three.js for 3D rendering and Socket.IO for real-time communication
- **Server**: Flask + Socket.IO backend (`polyclash/server.py`) that manages game rooms and relays moves
- **Game Logic**: The core rules and mechanics of the game (`polyclash/game/`)
- **AI**: The artificial intelligence that powers the computer opponent
- **CLI**: Unified command-line entry point (`polyclash`) with subcommands: `solo`, `family`, `team`, `serve`

## Getting Started

To get started with PolyClash, see the [Installation Guide](02_installation.md) and [Game Rules](03_game_rules.md).

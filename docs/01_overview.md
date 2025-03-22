# PolyClash Overview

## Introduction

PolyClash is a Go-like board game played on a spherical surface represented by a snub dodecahedron. The game combines the strategic depth of Go with the unique geometry of a spherical board, creating a novel gaming experience.

Like mathematical truth, Go is an eternal game in the universe. Similarly, the snub dodecahedron is also an eternal geometric shape, which is the Archimedean polyhedron with the most sphericity. PolyClash combines these two to create a new game with simple rules that make for interesting gameplay.

## Key Features

- **3D Spherical Board**: Play on a snub dodecahedron, providing a unique spherical Go experience
- **Multiple Game Modes**: Play locally against another human or AI, or play online against other players
- **3D Visualization**: Fully interactive 3D visualization of the game board using PyVista/VTK
- **AI Opponent**: Built-in AI that uses strategic algorithms to provide a challenging opponent
- **Network Play**: Play against other players over a local network or the internet
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Technical Overview

PolyClash is built using Python with the following key technologies:

- **PyQt5**: For the graphical user interface
- **PyVista/VTK**: For 3D visualization of the game board
- **Flask**: For the server component
- **Socket.IO**: For real-time communication during network play
- **Redis**: Optional backend for data storage in production environments

## Project Structure

The project is organized into several key components:

- **Client**: The desktop application that players use to play the game
- **Server**: The backend server that enables network play
- **Game Logic**: The core rules and mechanics of the game
- **GUI**: The graphical interface that displays the game board and allows player interaction
- **AI**: The artificial intelligence that powers the computer opponent
- **Network**: The components that enable multiplayer gameplay over a network

## Getting Started

To get started with PolyClash, see the [Installation Guide](02_installation.md) and [Game Rules](03_game_rules.md).

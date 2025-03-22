# Installation Guide

This guide will walk you through the process of installing and setting up PolyClash on your system.

## Prerequisites

Before installing PolyClash, ensure you have the following prerequisites:

- Python 3.10 or higher
- pip (Python package installer)
- Git (optional, for development)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The simplest way to install PolyClash is directly from the Python Package Index (PyPI):

```bash
pip install polyclash
```

This will install PolyClash and all its dependencies.

### Method 2: Install from Source

For development or to get the latest features, you can install PolyClash from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/spherical-go/polyclash.git
   cd polyclash
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Install development dependencies (optional):
   ```bash
   pip install -r requirements-dev.txt
   ```

## Dependencies

PolyClash depends on the following Python packages, which will be automatically installed:

- numpy (1.26.4)
- scipy (1.13.0)
- PyQt5 (5.15.10)
- pyvista (0.43.7)
- pyvistaqt (0.11.0)
- requests (2.32.0)
- python-socketio[client] (5.11.2)
- flask (3.0.3)
- flask-socketio (5.3.6)
- loguru (0.7.2)
- redis (5.0.4) (optional, for production server)

## Running PolyClash

### Running the Client

After installation, you can start the PolyClash client by running:

```bash
polyclash-client
```

This will launch the graphical user interface where you can play the game.

### Running the Server (Optional)

If you want to play over a network, you can start the PolyClash server:

```bash
polyclash-server
```

The server will start on port 3302 by default.

## Configuration

### Client Configuration

The client stores its configuration in the user's home directory:

- Windows: `%USERPROFILE%\.polyclash\`
- macOS/Linux: `~/.polyclash/`

### Server Configuration

For production deployment, see the [Deployment Guide](08_deployment.md).

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   If you encounter errors about missing dependencies, try reinstalling with:
   ```bash
   pip install --force-reinstall polyclash
   ```

2. **PyQt5 Installation Issues**:
   On some systems, PyQt5 might require additional system packages. Refer to the PyQt5 documentation for your specific operating system.

3. **3D Visualization Issues**:
   If you encounter problems with the 3D visualization, ensure your system has proper OpenGL support and updated graphics drivers.

### Getting Help

If you encounter any issues not covered here, please:

1. Check the [GitHub Issues](https://github.com/spherical-go/polyclash/issues) for similar problems
2. Open a new issue if your problem hasn't been reported

## Next Steps

Now that you have PolyClash installed, you can:

- Learn the [Game Rules](03_game_rules.md)
- Explore the [Architecture](04_architecture.md)
- Set up [Network Play](07_network_play.md)

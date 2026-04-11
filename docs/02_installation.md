# Installation Guide

This guide will walk you through the process of installing and setting up PolyClash on your system.

## Prerequisites

Before installing PolyClash, ensure you have the following prerequisites:

- Python 3.10 or higher
- pip or [uv](https://docs.astral.sh/uv/) (Python package installer)
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

2. Create a virtual environment and install (using `uv`):
   ```bash
   uv venv && source .venv/bin/activate
   uv pip install -e .
   ```

3. Install development dependencies (optional):
   ```bash
   uv pip install -e ".[dev]"
   ```

## Dependencies

PolyClash depends on the following Python packages, which will be automatically installed:

- numpy (2.3.3)
- scipy (1.16.2)
- requests (2.33.0)
- python-socketio[client] (5.13.0)
- flask (>=3.0,<3.1)
- flask-socketio (5.5.1)
- loguru (0.7.3)
- redis (6.4.0) (optional, for production server)

## Running PolyClash

PolyClash provides a single `polyclash` command with several subcommands:

### Solo Mode (vs AI)

Play against the AI locally. This starts a local server and opens your browser:

```bash
polyclash solo
polyclash solo --side white    # play as white
```

### Family Mode (LAN)

Start a game on your local network so two players can play from different devices:

```bash
polyclash family
polyclash family --white ai    # white is controlled by AI
```

The command prints URLs for both players and a viewer link.

### Team Mode (Self-Hosted Server)

Run a multi-room server with user accounts, invite codes, and a lobby:

```bash
polyclash team
polyclash team --rooms 4 --invites 10
```

Options include `--admin-user`, `--admin-pass`, `--db` (SQLite path), and `--rooms` (max simultaneous games).

### Serve Mode (Deployment)

Start a server for production or network deployment:

```bash
polyclash serve
polyclash serve --host 0.0.0.0 --port 3302
```

Use `--no-auth` to disable token authentication, or `--token <value>` to set a specific server token.

## Configuration

### Server Configuration

The server can be configured via command-line arguments and environment variables:

- `PORT`: Default port (default: 3302)
- `POLYCLASH_SERVER_TOKEN`: Server authentication token
- `POLYCLASH_MAX_ROOMS`: Maximum simultaneous games for team mode
- `POLYCLASH_ADMIN_USER` / `POLYCLASH_ADMIN_PASS`: Admin credentials for team mode
- `POLYCLASH_AUTH_DB`: Path to SQLite database for team mode user accounts
- `POLYCLASH_INVITES`: Number of initial invite codes for team mode

For production deployment, see the [Deployment Guide](09_deployment.md).

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   If you encounter errors about missing dependencies, try reinstalling with:
   ```bash
   pip install --force-reinstall polyclash
   ```

2. **Port Already in Use**:
   If port 3302 is taken, specify a different port:
   ```bash
   polyclash solo --port 3303
   ```

3. **Browser Not Opening**:
   If the browser does not open automatically, navigate to the URL printed in the terminal.

### Getting Help

If you encounter any issues not covered here, please:

1. Check the [GitHub Issues](https://github.com/spherical-go/polyclash/issues) for similar problems
2. Open a new issue if your problem hasn't been reported

## Next Steps

Now that you have PolyClash installed, you can:

- Learn the [Game Rules](03_game_rules.md)
- Explore the [Architecture](04_architecture.md)
- Set up [Network Play](07_network_play.md)

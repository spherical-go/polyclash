# Deployment Guide

PolyClash supports five deployment modes, from solo play to public internet hosting. Choose the mode that fits your needs.

## Prerequisites

- Python 3.10+ (for native installs)
- Docker and Docker Compose (for containerized deploys)

## Server Requirements

| Scenario | CPU | RAM | Disk |
|---|---|---|---|
| Solo / Home LAN | 1 core | 512 MB | 100 MB |
| Public / multiple games | 2+ cores | 1 GB+ | 200 MB |

---

## Mode 1: Solo Play

Play locally against AI or explore the board — no server needed.

```bash
pip install polyclash
polyclash solo
```

---

## Mode 2: Home / LAN (No Auth)

Run a server on your local network so friends can connect. No authentication, no Redis — uses in-memory storage.

### Native

```bash
pip install polyclash
polyclash serve --no-auth
```

The server listens on `http://localhost:3302` by default. To allow LAN connections:

```bash
polyclash serve --no-auth --host 0.0.0.0 --port 3302
```

### Docker

```bash
docker compose -f docker-compose.simple.yml up -d
```

Players connect to `http://<your-lan-ip>:3302`.

---

## Mode 3: Team Server (Recommended for Communities)

A self-hosted game server with user accounts, invite-code registration, a web lobby, and a configurable room limit. Like running your own Minecraft server.

### Quick Start — Native

```bash
pip install polyclash
polyclash team --rooms 8 --admin-pass YOUR_PASSWORD
```

The server will:
1. Create an admin account (`admin` / your password)
2. Generate 5 invite codes (printed to console)
3. Start the web lobby at `http://<your-ip>:3302/`

Share the invite codes with your friends. They register at the lobby, then create or join games.

### Quick Start — Docker Compose

```bash
docker compose up -d
```

On first run, check the logs for the admin password and invite codes:

```bash
docker compose logs polyclash | head -20
```

### Configuration

All settings can be set via CLI flags or environment variables:

| Flag | Env Var | Default | Description |
|------|---------|---------|-------------|
| `--rooms` | `POLYCLASH_MAX_ROOMS` | `8` | Max simultaneous games |
| `--admin-user` | `POLYCLASH_ADMIN_USER` | `admin` | Admin username |
| `--admin-pass` | `POLYCLASH_ADMIN_PASS` | auto-generated | Admin password |
| `--invites` | `POLYCLASH_INVITES` | `5` | Invite codes to generate on startup |
| `--db` | `POLYCLASH_AUTH_DB` | `polyclash_users.db` | SQLite database path |
| `--port` | `PORT` | `3302` | Server port |

### Managing Users

Log in as admin in the web lobby to:
- Generate new invite codes
- View all users and invite code usage

### State and Restarts

All game state (rooms, boards, users) lives in memory. A server restart resets everything — admin credentials and invite codes are regenerated and printed to the logs. This is by design for a small team server: simple, no external storage needed.

---

## Mode 4: One-Click Cloud Deployment

Deploy to Railway, Render, or Fly.io. The server runs in team mode. State resets on each deploy — check logs for new admin credentials and invite codes.

### Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/_6HDwH)

After deployment:
1. Check deployment logs for admin credentials (`admin` / auto-generated password) and invite codes
2. Optionally set `POLYCLASH_ADMIN_PASS` in Variables to use a fixed password

### Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/spherical-go/polyclash)

Render auto-configures:
- Auto-generated admin password (visible in dashboard → Environment)
- Check deployment logs for invite codes

### Fly.io

```bash
fly launch --copy-config
fly secrets set POLYCLASH_ADMIN_PASS=your-password
fly deploy
```

### Environment Variables for Cloud

Set these in your cloud platform's dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `POLYCLASH_ADMIN_PASS` | Recommended | Admin password (auto-generated if unset) |
| `POLYCLASH_MAX_ROOMS` | No | Room limit (default: 8) |
| `POLYCLASH_INVITES` | No | Invite codes to generate (default: 5) |

---

## Mode 5: Public / Internet (Self-Hosted)

For internet-facing deployments on your own server, use Docker Compose with an nginx reverse proxy and HTTPS.

### 1. Start the services

Create a `.env` file with team-mode variables:

```bash
POLYCLASH_ADMIN_PASS=your-secure-password
POLYCLASH_MAX_ROOMS=16
POLYCLASH_INVITES=10
```

```bash
docker compose up -d
```

This starts:
- **polyclash** on port 3302 (internal)
- **redis** on port 6379 (internal)

### 2. Configure nginx reverse proxy

Install nginx and create `/etc/nginx/sites-available/polyclash`:

```nginx
server {
    listen 80;
    server_name polyclash.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name polyclash.example.com;

    ssl_certificate     /etc/letsencrypt/live/polyclash.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/polyclash.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3302;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:3302/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
        proxy_buffering off;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/polyclash /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Obtain an SSL certificate

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d polyclash.example.com
sudo systemctl enable certbot.timer
```

### 4. Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Docker Files Reference

| File | Purpose |
|---|---|
| `Dockerfile` | Builds the server image, default team mode |
| `docker-compose.yml` | Team server (no Redis, in-memory state) |
| `docker-compose.simple.yml` | Minimal: solo/LAN, no auth, no Redis |
| `render.yaml` | Render.com deploy blueprint |
| `railway.json` | Railway deploy config |
| `fly.toml` | Fly.io deploy config |
| `.dockerignore` | Excludes dev artifacts from the build context |

---

## Redis

Redis is **optional**. Without Redis, the server uses in-memory storage — all state (games, boards, users) resets on restart. With Redis, game and board state persists across restarts via `save_board()` / `restore_boards()`. For a small team server with 8 rooms, in-memory mode is sufficient.

To use Redis with a native install:

```bash
# Install Redis
sudo apt install redis-server   # Debian/Ubuntu
brew install redis               # macOS

# Start Redis
sudo systemctl start redis
```

The server auto-detects Redis on `localhost:6379`.

---

## Monitoring and Maintenance

### Logs

```bash
# Docker
docker compose logs -f polyclash

# Native
# Logs go to stdout via loguru
```

### Updating

```bash
# Docker
docker compose pull
docker compose up -d --build

# Native
pip install --upgrade polyclash
```

### Redis Backup

```bash
redis-cli save
cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb
```

---

## Troubleshooting

| Problem | Check |
|---|---|
| Server won't start | Port 3302 in use? Redis running (if expected)? |
| Clients can't connect | Firewall rules? Correct host/port? |
| WebSocket fails | nginx `Upgrade` headers configured? |
| Games lost on restart | By design — in-memory state resets on restart; use Redis for persistence |
| Can't find admin password | Check server logs; set `POLYCLASH_ADMIN_PASS` env var |
| Invite codes not showing | Check server startup logs; set `POLYCLASH_INVITES` > 0 |
| Lobby shows "Team mode not enabled" | Server not started with `polyclash team` |

For more help, see [GitHub Issues](https://github.com/spherical-go/polyclash/issues).

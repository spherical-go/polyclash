# Deployment Guide

PolyClash supports four deployment modes, from solo play to public internet hosting. Choose the mode that fits your needs.

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
polyclash play
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

## Mode 3: Team / LAN with Auth

Add a shared token so only authorized players can connect.

### Native

```bash
polyclash serve --host 0.0.0.0 --port 3302 --token YOUR_SECRET_TOKEN
```

Players must provide the token when connecting.

### Docker

```bash
POLYCLASH_SERVER_TOKEN=YOUR_SECRET_TOKEN docker compose up -d
```

This starts both the PolyClash server and a Redis instance for persistent storage.

---

## Mode 4: Public / Internet

For internet-facing deployments, use Docker Compose with an nginx reverse proxy and HTTPS.

### 1. Start the services

Create a `.env` file:

```bash
POLYCLASH_SERVER_TOKEN=your-secure-random-token
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
| `Dockerfile` | Builds the server image (no Qt/PyVista) |
| `docker-compose.yml` | Full stack: PolyClash + Redis |
| `docker-compose.simple.yml` | Minimal: PolyClash only, no auth |
| `.dockerignore` | Excludes dev artifacts from the build context |

---

## Redis

Redis is **optional**. When available, it provides persistent game storage across server restarts. Without Redis, the server uses in-memory storage (games are lost on restart).

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
| Games lost on restart | Redis not running — data was in-memory only |

For more help, see [GitHub Issues](https://github.com/spherical-go/polyclash/issues).

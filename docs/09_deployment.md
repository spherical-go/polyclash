# Deployment Guide

This document provides instructions for deploying PolyClash in a production environment, including server setup, configuration, and maintenance.

## Overview

PolyClash can be deployed in various environments, from a simple local setup to a full production server accessible over the internet. This guide focuses on setting up a production server for hosting network games.

## Prerequisites

Before deploying PolyClash, ensure you have:

1. A server with Python 3.10 or higher installed
2. A domain name (optional, but recommended for internet-facing servers)
3. Basic knowledge of server administration and networking

## Server Requirements

The server requirements depend on the expected number of concurrent games:

- **CPU**: 1+ cores (2+ recommended for multiple concurrent games)
- **RAM**: 512MB+ (1GB+ recommended for multiple concurrent games)
- **Disk**: 100MB+ for the application and logs
- **Network**: Stable internet connection with open ports for HTTP/WebSocket traffic

## Installation

### Install PolyClash

Install PolyClash on the server:

```bash
pip install polyclash
```

### Install Production Dependencies

Install additional dependencies for production:

```bash
pip install uwsgi gevent redis
```

## Configuration

### Server Configuration

Create a configuration directory:

```bash
mkdir -p ~/.polyclash
```

Create a configuration file (`~/.polyclash/config.ini`):

```ini
[server]
host = 0.0.0.0
port = 7763
debug = false

[storage]
type = redis
host = localhost
port = 6379
db = 0

[logging]
level = INFO
file = ~/.polyclash/server.log
```

### Redis Setup

If you're using Redis for storage (recommended for production):

1. Install Redis:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server

   # CentOS/RHEL
   sudo yum install redis

   # macOS
   brew install redis
   ```

2. Start Redis:
   ```bash
   # Ubuntu/Debian/CentOS/RHEL
   sudo systemctl start redis

   # macOS
   brew services start redis
   ```

3. Configure Redis to start on boot:
   ```bash
   # Ubuntu/Debian/CentOS/RHEL
   sudo systemctl enable redis

   # macOS
   brew services start redis
   ```

## Running the Server

### Development Mode

For testing, you can run the server directly:

```bash
polyclash-server
```

### Production Mode with uWSGI

For production, use uWSGI to run the server:

```bash
uwsgi --http :7763 --gevent 100 --http-websockets --master --wsgi polyclash.server:app --logto ~/.polyclash/uwsgi.log
```

Create a uWSGI configuration file (`~/.polyclash/uwsgi.ini`):

```ini
[uwsgi]
http = :7763
gevent = 100
http-websockets = true
master = true
wsgi-file = /path/to/polyclash/server.py
callable = app
processes = 1
threads = 2
logto = ~/.polyclash/uwsgi.log
```

Then run:

```bash
uwsgi --ini ~/.polyclash/uwsgi.ini
```

### Systemd Service

For systems using systemd, create a service file (`/etc/systemd/system/polyclash.service`):

```ini
[Unit]
Description=PolyClash Server
After=network.target

[Service]
User=your_username
Group=your_group
WorkingDirectory=/home/your_username
ExecStart=/usr/local/bin/uwsgi --ini /home/your_username/.polyclash/uwsgi.ini
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/your_username

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable polyclash
sudo systemctl start polyclash
```

## Nginx Configuration

For production deployments, it's recommended to use Nginx as a reverse proxy in front of the uWSGI server:

1. Install Nginx:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nginx

   # CentOS/RHEL
   sudo yum install nginx

   # macOS
   brew install nginx
   ```

2. Create a Nginx configuration file (`/etc/nginx/sites-available/polyclash`):
   ```nginx
   server {
       listen 80;
       server_name polyclash.example.com;

       location /sphgo {
           proxy_pass http://127.0.0.1:7763;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /socket.io {
           proxy_redirect off;
           proxy_buffering off;

           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "Upgrade";

           proxy_pass http://127.0.0.1:7763/socket.io;
       }
   }
   ```

3. Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/polyclash /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## SSL/TLS Configuration

For secure communication, configure SSL/TLS with Let's Encrypt:

1. Install Certbot:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install certbot python3-certbot-nginx

   # CentOS/RHEL
   sudo yum install certbot python3-certbot-nginx
   ```

2. Obtain a certificate:
   ```bash
   sudo certbot --nginx -d polyclash.example.com
   ```

3. Certbot will automatically update your Nginx configuration to use HTTPS.

4. Set up automatic renewal:
   ```bash
   sudo systemctl enable certbot.timer
   sudo systemctl start certbot.timer
   ```

## Firewall Configuration

Configure your firewall to allow the necessary traffic:

```bash
# Ubuntu/Debian with UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL with firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Monitoring and Maintenance

### Logging

PolyClash logs are stored in:
- `~/.polyclash/server.log`: Server logs
- `~/.polyclash/uwsgi.log`: uWSGI logs

Monitor these logs for errors and issues.

### Backup

Regularly backup your Redis data:

```bash
# Create a Redis backup
redis-cli save

# Copy the dump.rdb file to a backup location
cp /var/lib/redis/dump.rdb /backup/redis-backup-$(date +%Y%m%d).rdb
```

### Monitoring

Monitor your server's health using tools like:
- Prometheus
- Grafana
- Nagios
- Zabbix

Set up alerts for:
- High CPU usage
- High memory usage
- Disk space running low
- Server unreachable

### Updating

To update PolyClash:

```bash
pip install --upgrade polyclash
sudo systemctl restart polyclash
```

## Scaling

### Horizontal Scaling

For high-traffic deployments, you can scale horizontally:

1. Set up multiple PolyClash servers
2. Configure a load balancer (like HAProxy or Nginx) in front of them
3. Use a shared Redis instance for storage

Example HAProxy configuration:

```
frontend polyclash_frontend
    bind *:80
    mode http
    default_backend polyclash_backend

backend polyclash_backend
    mode http
    balance roundrobin
    option httpchk GET /sphgo/
    server server1 192.168.1.1:7763 check
    server server2 192.168.1.2:7763 check
```

### Vertical Scaling

You can also scale vertically by:
- Increasing the number of uWSGI processes and threads
- Allocating more CPU and RAM to the server
- Optimizing Redis configuration

## Troubleshooting

### Common Issues

1. **Server won't start**:
   - Check the logs for errors
   - Verify that the required ports are not in use
   - Ensure that Redis is running (if using Redis storage)

2. **Clients can't connect**:
   - Check that the server is running
   - Verify that the firewall allows connections
   - Ensure that the domain name resolves to the correct IP address

3. **WebSocket connection fails**:
   - Check the Nginx configuration for WebSocket support
   - Verify that the proxy headers are set correctly
   - Ensure that the client is using the correct URL

### Getting Help

If you encounter issues not covered here:
1. Check the [GitHub Issues](https://github.com/spherical-go/polyclash/issues) for similar problems
2. Open a new issue if your problem hasn't been reported

## Security Considerations

### Server Hardening

1. Keep the server updated with security patches
2. Use a firewall to restrict access
3. Implement fail2ban to prevent brute force attacks
4. Use strong passwords and key-based authentication
5. Disable unnecessary services

### Application Security

1. Keep PolyClash and its dependencies updated
2. Use HTTPS for all communication
3. Implement rate limiting to prevent abuse
4. Monitor logs for suspicious activity
5. Regularly backup data

## Performance Tuning

### uWSGI Tuning

Optimize uWSGI configuration for better performance:

```ini
[uwsgi]
http = :7763
gevent = 100
http-websockets = true
master = true
wsgi-file = /path/to/polyclash/server.py
callable = app
processes = 2
threads = 4
listen = 1024
max-requests = 5000
harakiri = 30
logto = ~/.polyclash/uwsgi.log
```

### Redis Tuning

Optimize Redis configuration for better performance:

```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Nginx Tuning

Optimize Nginx configuration for better performance:

```nginx
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
gzip on;
```

## Conclusion

By following this guide, you should have a robust, secure, and performant PolyClash server deployment. Remember to monitor your server regularly and keep all software updated to ensure the best experience for your players.

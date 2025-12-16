# GitWatch Docker Deployment Guide

**VPS Host:** 31.97.232.229  
**Domain:** gitwatch.vishnupraksh.in  
**Data Directory:** /gitwatch  
**Container Port:** 8050 (internal, exposed via nginx-proxy)

---

## Prerequisites

- SSH access: `ssh root@31.97.232.229`
- Docker & Docker Compose installed on VPS
- Domain DNS pointing to VPS IP (31.97.232.229)

---

## Initial Deployment

### 1. SSH into VPS
```bash
ssh root@31.97.232.229
```

### 2. Create data directory
```bash
mkdir -p /gitwatch/repos
chmod -R 755 /gitwatch
```

### 3. Clone or transfer GitWatch repository
```bash
cd /home
git clone <your-repo-url> gitwatch
cd gitwatch
```

Or if uploading files locally:
```bash
# From your local machine
scp -r ./* root@31.97.232.229:/home/gitwatch/
```

### 4. Create necessary files

If not present, create/verify these files exist in the deployment directory:
- `Dockerfile`
- `docker-compose.yml`
- `app.py`
- `config.py`
- `db.py`
- `git_utils.py`
- `requirements.txt`

### 5. Build Docker image
```bash
cd /home/gitwatch
docker build -t gitwatch:latest .
```

### 6. Update docker-compose.yml email
Edit `docker-compose.yml` and replace `your-email@example.com` with your actual email:
```bash
nano docker-compose.yml
```

Find the line:
```yaml
- LETSENCRYPT_EMAIL=your-email@example.com
```

Change to your email, then save (Ctrl+O, Enter, Ctrl+X).

### 7. Start all containers
```bash
cd /home/gitwatch
docker-compose up -d
```

This will:
- Start GitWatch on internal port 8050
- Start nginx-proxy (reverse proxy on ports 80, 443)
- Start ACME companion (auto-SSL via Let's Encrypt)

### 8. Verify deployment
```bash
# Check if all containers are running
docker ps

# Output should show:
# - gitwatch
# - nginx-proxy
# - acme-companion
```

### 9. Check SSL certificate generation (takes 30-60 seconds)
```bash
docker logs acme-companion | tail -20
```

Wait for message like: `Successfully issued certificate for gitwatch.vishnupraksh.in`

### 10. Test the application
```bash
# Wait 60 seconds for SSL cert generation, then visit in browser:
https://gitwatch.vishnupraksh.in
```

**Default Credentials:**
- Username: `admin`
- Password: `admin`

Change admin password immediately after first login!

---

## Daily Operations

### Check application status
```bash
docker ps
```

### View application logs
```bash
docker logs -f gitwatch
```

### View nginx-proxy logs
```bash
docker logs -f nginx-proxy
```

### View ACME/SSL logs
```bash
docker logs acme-companion | tail -50
```

### Stop all containers (keep data)
```bash
cd /home/gitwatch
docker-compose down
```

### Restart all containers
```bash
cd /home/gitwatch
docker-compose restart
```

### Restart only GitWatch app
```bash
docker restart gitwatch
```

### Stop only GitWatch app (keep nginx-proxy running)
```bash
docker stop gitwatch
```

### Start only GitWatch app
```bash
docker start gitwatch
```

---

## Configuration & Data

### Database location
```
/gitwatch/gitwatch.db
```

### Repository scan directory
```
/gitwatch/repos
```

All repositories should be cloned/initialized into `/gitwatch/repos/` on the VPS:
```bash
cd /gitwatch/repos
git clone <repo-url> <repo-name>
```

### Update environment variables
Edit `docker-compose.yml` and modify environment section under `gitwatch` service:
```yaml
environment:
  - GITWATCH_DATA_DIR=/data/gitwatch
  - GITWATCH_REPOS_PATH=/data/gitwatch/repos
  - VIRTUAL_HOST=gitwatch.vishnupraksh.in
  - LETSENCRYPT_HOST=gitwatch.vishnupraksh.in
```

Then restart:
```bash
cd /home/gitwatch
docker-compose down && docker-compose up -d
```

---

## Updating Application

### Pull latest code
```bash
cd /home/gitwatch
git pull origin main
```

### Rebuild Docker image
```bash
docker build -t gitwatch:latest .
```

### Restart container with new image
```bash
cd /home/gitwatch
docker-compose down
docker-compose up -d
```

---

## Troubleshooting

### Application won't start
```bash
# Check logs
docker logs gitwatch

# Check if port 8050 is accessible
docker exec gitwatch curl http://localhost:8050
```

### SSL certificate not issued
```bash
# Check ACME logs
docker logs acme-companion

# Verify domain DNS points to VPS
nslookup gitwatch.vishnupraksh.in

# Common issues:
# - Email address invalid
# - Domain DNS not pointing to VPS
# - Port 80/443 blocked by firewall
```

### nginx-proxy not routing traffic
```bash
# Restart all containers
cd /home/gitwatch
docker-compose restart

# Check nginx-proxy config
docker exec nginx-proxy cat /etc/nginx/conf.d/default.conf | grep gitwatch
```

### Database locked error
```bash
# Stop and restart container
docker stop gitwatch
docker start gitwatch
```

### Out of disk space
```bash
# Check usage
df -h

# Clean unused Docker images
docker image prune -a

# Clean unused volumes
docker volume prune
```

---

## Backup & Restore

### Backup database and data
```bash
tar -czf gitwatch-backup-$(date +%Y%m%d).tar.gz /gitwatch/
```

### Transfer backup to local machine
```bash
# From local machine
scp root@31.97.232.229:/home/gitwatch-backup-*.tar.gz .
```

### Restore from backup
```bash
cd /
tar -xzf gitwatch-backup-20251216.tar.gz
docker-compose restart
```

---

## Monitoring & Maintenance

### Check container resource usage
```bash
docker stats gitwatch
```

### View SSL certificate expiration
```bash
docker exec acme-companion ls -la /etc/acme.sh/gitwatch.vishnupraksh.in_ecc/
```

### Renew SSL certificates manually
```bash
docker restart acme-companion
```

### Clean up old Docker layers (after updates)
```bash
docker system prune
```

---

## Common Commands Reference

| Task | Command |
|------|---------|
| Deploy | `cd /home/gitwatch && docker-compose up -d` |
| Stop | `docker-compose down` |
| Logs | `docker logs -f gitwatch` |
| Restart app | `docker restart gitwatch` |
| Restart all | `docker-compose restart` |
| View status | `docker ps` |
| SSH into VPS | `ssh root@31.97.232.229` |
| Access app | `https://gitwatch.vishnupraksh.in` |

---

## Notes

- Data persists in `/gitwatch` directory
- Database is SQLite (file-based, no external DB needed)
- SSL certificates auto-renew via Let's Encrypt
- Admin user created on first run (change password!)
- All app and repository data survives container restarts

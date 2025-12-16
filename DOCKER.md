# 🐋 Docker Deployment Guide

Run Hammy the Hire Tracker in a Docker container for easy, consistent deployment across any platform.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- Your configuration files ready:
  - `config.yaml` (copy from `config.example.yaml`)
  - `.env` with your `ANTHROPIC_API_KEY`
  - `credentials.json` from Google Cloud Console
  - Resume files in `resumes/` directory

## Quick Start

### 1. **Prepare Configuration**

```bash
# Copy example files
cp config.example.yaml config.yaml
cp .env.example .env

# Edit config.yaml with your information
nano config.yaml  # or use your preferred editor

# Add your Anthropic API key to .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# Set up your resumes
cp resumes/templates/*.txt resumes/
# Then edit the resume files with your information
```

### 2. **Create Data Directory**

```bash
mkdir -p data backups cover_letters
```

### 3. **Build and Run**

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Access the dashboard at http://localhost:5000
```

### 4. **Gmail OAuth Setup**

On first run, you'll need to authenticate with Gmail:

```bash
# Check logs for the OAuth URL
docker-compose logs hammy

# The logs will show a URL to visit for authentication
# Complete the OAuth flow in your browser
# The token will be saved to ./data/token.json
```

## Docker Commands

### Basic Operations

```bash
# Start the container
docker-compose up -d

# Stop the container
docker-compose down

# Restart the container
docker-compose restart

# View logs (real-time)
docker-compose logs -f

# View logs (last 100 lines)
docker-compose logs --tail=100
```

### Maintenance

```bash
# Rebuild after code changes
docker-compose build
docker-compose up -d

# Access container shell
docker-compose exec hammy /bin/bash

# View container status
docker-compose ps

# Check container health
docker inspect --format='{{.State.Health.Status}}' hammy-hire-tracker
```

### Data Management

```bash
# Backup database
cp data/jobs.db data/jobs_backup_$(date +%Y%m%d).db

# View database size
du -h data/jobs.db

# Clean up old backups
rm data/backups/backup_*.db
```

## Volume Mounts

The docker-compose.yml mounts several directories:

| Host Path | Container Path | Purpose | Mode |
|-----------|---------------|---------|------|
| `./config.yaml` | `/app/config.yaml` | User configuration | Read-only |
| `./.env` | `/app/.env` | Environment variables | Read-only |
| `./credentials.json` | `/app/credentials.json` | Gmail OAuth credentials | Read-only |
| `./data/jobs.db` | `/app/jobs.db` | SQLite database | Read-write |
| `./data/token.json` | `/app/token.json` | Gmail OAuth token | Read-write |
| `./resumes/` | `/app/resumes/` | Your resume files | Read-only |
| `./cover_letters/` | `/app/cover_letters/` | Generated cover letters | Read-write |
| `./data/backups/` | `/app/backups/` | Database backups | Read-write |

## Environment Variables

Configure these in your `.env` file:

```env
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional
DB_PATH=/app/data/jobs.db
FLASK_ENV=production
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs hammy

# Common issues:
# 1. Missing config.yaml
cp config.example.yaml config.yaml

# 2. Missing .env file
cp .env.example .env
# Then add your ANTHROPIC_API_KEY

# 3. Port 5000 already in use
# Change port in docker-compose.yml: "5001:5000"
```

### Gmail Authentication Issues

```bash
# Remove existing token and re-authenticate
rm data/token.json
docker-compose restart

# Check for credentials.json
ls -la credentials.json

# Ensure credentials.json is valid JSON
cat credentials.json | python -m json.tool
```

### Database Issues

```bash
# Check database file permissions
ls -la data/jobs.db

# Reset database (WARNING: deletes all data)
docker-compose down
rm data/jobs.db
docker-compose up -d
```

### Container Health Check Failing

```bash
# Check health status
docker inspect --format='{{json .State.Health}}' hammy-hire-tracker | python -m json.tool

# Check if Flask is running inside container
docker-compose exec hammy curl http://localhost:5000

# View Flask error logs
docker-compose logs hammy | grep ERROR
```

## Production Deployment

### Using Named Volumes

For better data persistence, use Docker named volumes:

```yaml
# In docker-compose.yml, replace bind mounts with:
volumes:
  - hammy-config:/app/config:ro
  - hammy-data:/app/data

volumes:
  hammy-config:
  hammy-data:
```

### Resource Limits

Add resource constraints to prevent excessive resource usage:

```yaml
services:
  hammy:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Running on a Different Port

```yaml
# In docker-compose.yml
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

### Automatic Restarts

The container is configured with `restart: unless-stopped`, meaning it will:
- Restart automatically if it crashes
- Restart on system reboot
- NOT restart if you manually stop it

## Updating Hammy

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify it's running
docker-compose ps
```

## Uninstalling

```bash
# Stop and remove container
docker-compose down

# Remove container and images
docker-compose down --rmi all

# Remove all data (WARNING: permanent)
docker-compose down -v
rm -rf data/ backups/ cover_letters/
```

## Advanced: Multi-User Setup

To run multiple instances for different users:

```bash
# Create separate directories
mkdir hammy-user1 hammy-user2

# Copy configs to each
cp -r . hammy-user1/
cp -r . hammy-user2/

# Edit docker-compose.yml in each to use different ports
# User 1: ports: "5000:5000"
# User 2: ports: "5001:5000"

# Start each instance
cd hammy-user1 && docker-compose up -d
cd ../hammy-user2 && docker-compose up -d
```

## Support

For Docker-specific issues:
- Check logs: `docker-compose logs -f`
- Inspect container: `docker inspect hammy-hire-tracker`
- Check Docker version: `docker --version && docker-compose --version`

For application issues, see the main [README.md](README.md).

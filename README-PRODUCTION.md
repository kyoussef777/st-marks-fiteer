# HeBrews Coffee Cart - Production Deployment Guide

This guide explains how to deploy the HeBrews Coffee Cart application in production on a Docker VM in Proxmox.

## Prerequisites

- Docker and Docker Compose installed on your Proxmox VM
- At least 2GB RAM and 10GB storage
- Network access for downloading Docker images

## Quick Start

1. **Clone the repository** (or upload files to your VM):
   ```bash
   git clone <repository-url>
   cd hebrews-coffee
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.prod .env
   nano .env
   ```
   Update the following values:
   - `FLASK_SECRET_KEY`: Generate a secure random key
   - `APP_USERNAME`: Your admin username
   - `APP_PASSWORD`: Your secure admin password

3. **Create required directories**:
   ```bash
   mkdir -p logs ssl
   ```

4. **Deploy the application**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Access the application**:
   - Open your browser and navigate to `http://your-vm-ip`
   - Login with the credentials you set in the `.env` file

## Production Features

### Security
- **Non-root container**: Application runs as non-privileged user
- **Rate limiting**: 10 requests per second with burst capacity
- **Security headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **CSRF protection**: All forms protected against CSRF attacks

### Performance
- **Gunicorn WSGI server**: Production-grade Python web server
- **Nginx reverse proxy**: Load balancing and static file serving
- **Health checks**: Automatic container health monitoring
- **Log rotation**: Prevents log files from growing too large

### Reliability
- **Persistent data**: Database stored in Docker volume
- **Auto-restart**: Containers restart automatically on failure
- **Graceful shutdown**: Proper signal handling for clean shutdowns

## Configuration Options

### Environment Variables
```bash
FLASK_SECRET_KEY=your-super-secret-production-key-here
FLASK_ENV=production
APP_USERNAME=admin
APP_PASSWORD=your-secure-password-here
```

### SSL/HTTPS Setup (Optional)
1. Place your SSL certificates in the `ssl/` directory:
   - `ssl/cert.pem` - SSL certificate
   - `ssl/key.pem` - Private key

2. Uncomment the HTTPS server block in `nginx.conf`

3. Update your domain name in the configuration

4. Restart the containers:
   ```bash
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

## Monitoring and Maintenance

### View Logs
```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs hebrews-coffee

# Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f
```

### Health Checks
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check application health
curl http://your-vm-ip/health
```

### Database Backup
```bash
# Create backup
docker run --rm -v hebrews-coffee_hebrews_data:/data -v $(pwd):/backup alpine tar czf /backup/backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Restore backup
docker run --rm -v hebrews-coffee_hebrews_data:/data -v $(pwd):/backup alpine tar xzf /backup/backup-YYYYMMDD-HHMMSS.tar.gz -C /data
```

### Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Check environment variables in `.env`
   - Verify Docker has enough resources
   - Check logs: `docker-compose -f docker-compose.prod.yml logs`

2. **Can't access from external network**:
   - Verify Proxmox firewall settings
   - Check VM network configuration
   - Ensure port 80 (and 443 for HTTPS) are open

3. **Database issues**:
   - Check volume permissions
   - Verify data directory exists and is writable
   - Check available disk space

4. **Performance issues**:
   - Monitor resource usage: `docker stats`
   - Increase worker count in Dockerfile.prod
   - Add more RAM to the VM

### Performance Tuning

For high-traffic deployments:

1. **Increase Gunicorn workers**:
   Edit `Dockerfile.prod` and change `--workers 2` to `--workers 4`

2. **Add Redis for session storage**:
   Add Redis service to docker-compose.prod.yml

3. **Use external database**:
   Replace SQLite with PostgreSQL for better concurrent performance

## Security Considerations

- Change default credentials immediately
- Use strong, unique passwords
- Keep Docker and system updated
- Monitor access logs regularly
- Consider using a firewall
- Enable HTTPS in production
- Regular security audits

## Support

For issues or questions:
1. Check the logs first
2. Review this documentation
3. Check the main README.md for application-specific help

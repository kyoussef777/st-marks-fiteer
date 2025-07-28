# Production Docker Setup Guide

## Quick Setup Instructions

### 1. Prerequisites
- Docker and Docker Compose installed
- `.env` file with required environment variables

### 2. Environment Variables
Make sure your `.env` file contains:
```bash
FLASK_SECRET_KEY=your-secret-key-here
APP_USERNAME=admin
APP_PASSWORD=your-secure-password
DOMAIN=localhost
```

### 3. Start Production Environment
```bash
# Start the production containers
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker logs hebrews-coffee-prod
```

### 4. Access the Application
- **Main Application**: http://localhost:3001
- **Direct App Access**: http://localhost:3000 (bypasses nginx)

### 5. Login Credentials
- **Username**: admin (or whatever you set in APP_USERNAME)
- **Password**: password (or whatever you set in APP_PASSWORD)

### 6. Troubleshooting Commands
```bash
# Stop containers
docker-compose -f docker-compose.prod.yml down

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up --build -d

# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Check container health
docker-compose -f docker-compose.prod.yml ps
```

### 7. Data Persistence
- Database is stored in Docker volume `hebrews_data`
- Logs are stored in `./logs` directory
- Data persists between container restarts

### 8. Production Features
- ✅ Nginx reverse proxy with security headers
- ✅ Gunicorn WSGI server for production performance
- ✅ Health checks and automatic restarts
- ✅ Persistent data storage
- ✅ Comprehensive SQL injection protection
- ✅ Input validation and sanitization
- ✅ CSRF protection
- ✅ Secure session management

## Current Status
🟢 **WORKING** - Application is running successfully at http://localhost:3001

The internal server error has been resolved by:
1. Setting correct database path (`DATABASE_PATH=/app/data/db.sqlite3`)
2. Using Docker volume for persistent storage
3. Proper environment variable configuration

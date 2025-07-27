#!/bin/bash

echo "Cleaning up Docker containers and images..."

# Stop and remove all containers for this project
docker-compose -f docker-compose.prod.yml down --remove-orphans

# Remove any dangling containers
docker container prune -f

# Remove the specific images if they exist
docker rmi hebrews-coffee_hebrews-coffee 2>/dev/null || true
docker rmi hebrews-coffee-prod 2>/dev/null || true

# Remove dangling images
docker image prune -f

# Remove any volumes if needed (be careful with this)
# docker volume prune -f

echo "Rebuilding and starting services..."

# Rebuild and start
docker-compose -f docker-compose.prod.yml up --build -d

echo "Done! Check the status with: docker-compose -f docker-compose.prod.yml ps"

@echo off
echo ========================================
echo IshemaLink Deployment Script
echo ========================================

echo Pulling latest code...
git pull origin main

echo Building Docker images...
docker-compose build

echo Stopping old containers...
docker-compose down

echo Starting new containers...
docker-compose up -d

echo Running migrations...
docker-compose exec -T web python manage.py migrate --noinput

echo Collecting static files...
docker-compose exec -T web python manage.py collectstatic --noinput

echo Checking health...
timeout /t 5 /nobreak
curl -f http://localhost/api/health/

echo ========================================
echo Deployment Complete!
echo ========================================
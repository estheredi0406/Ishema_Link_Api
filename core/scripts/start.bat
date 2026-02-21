@echo off
echo Starting IshemaLink API...
docker-compose up -d
echo.
echo All services started!
echo API: http://localhost
echo Admin: http://localhost/admin
echo.
echo View logs: docker-compose logs -f
@echo off
setlocal enabledelayedexpansion

set BACKUP_DIR=backups
set DATE=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set DATE=%DATE: =0%
set BACKUP_FILE=%BACKUP_DIR%/ishemalink_backup_%DATE%.sql

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo Creating database backup...
docker-compose exec -T db pg_dump -U ishema ishemalink > %BACKUP_FILE%

echo Backup created: %BACKUP_FILE%
echo Done!
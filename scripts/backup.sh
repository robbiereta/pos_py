#!/bin/bash

# Load environment variables
source ../.env.staging

# Set backup directory
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"

# Create backup
docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -delete

# Log backup status
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}.gz"
else
    echo "Backup failed!"
    exit 1
fi

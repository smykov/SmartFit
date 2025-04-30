#!/bin/bash

# Конфигурация
BACKUP_DIR="/backup/smartfit"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
POSTGRES_CONTAINER="smartfit-postgres"
RETENTION_DAYS=7

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR/{postgres,firebase}

# Бэкап PostgreSQL
echo "Backing up PostgreSQL..."
docker exec $POSTGRES_CONTAINER pg_dumpall -U $POSTGRES_USER > $BACKUP_DIR/postgres/backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/postgres/backup_$TIMESTAMP.sql

# Бэкап Firebase конфигурации
echo "Backing up Firebase configuration..."
cp /path/to/firebase-credentials.json $BACKUP_DIR/firebase/firebase_$TIMESTAMP.json

# Удаление старых бэкапов
echo "Cleaning old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Загрузка на удаленное хранилище (опционально)
if [ "$UPLOAD_TO_S3" = "true" ]; then
    aws s3 sync $BACKUP_DIR s3://$S3_BUCKET/backups/
fi

echo "Backup completed!"
#!/bin/bash

# Docker PostgreSQL
DOCKER_SERVICE_NAME="db"
DOCKER_DB_NAME="$1"
DOCKER_DB_USER="$2"
DOCKER_DB_PASSWORD="$3"


# Optional: fallback/default check
if [ -z "$3" ]; then
  echo "Usage: $0 <local_db> <local_user> <local_password>"
  exit 1
fi


BACKUP_FILE_BASE="db_backup.sql"
CHUNK_PREFIX="db_backup_part_"

BACKUP_FILE_BASE="db/full_restore.sql"

# ========== Step1: Copy & Restore in Docker ==========
DOCKER_CONTAINER_NAME=$(docker compose ps -q "$DOCKER_SERVICE_NAME")
if [ -z "$DOCKER_CONTAINER_NAME" ]; then
    echo "❌ Docker container for service '$DOCKER_SERVICE_NAME' not found."
    exit 1
fi

echo "📤 Merging backup files into a single file..."
cat db/${CHUNK_PREFIX}*.sql > "$BACKUP_FILE_BASE"

echo "🧹 Remove temporary chunk files..."
rm db/${CHUNK_PREFIX}*.sql


echo "🛠 Reassembling and restoring inside container..."
docker exec -e PGPASSWORD="$DOCKER_DB_PASSWORD" "$DOCKER_CONTAINER_NAME" \
    bash -c "psql -U $DOCKER_DB_USER -d $DOCKER_DB_NAME -f /tmp/full_restore.sql"

if [ $? -ne 0 ]; then
    echo "❌ Restore failed."
    exit 1
fi
echo "✅ Restore completed."

# ========== Step 4: Cleanup ==========
echo "🧹 Cleaning up local backup files..."
#echo -n "--" > "$BACKUP_FILE_BASE"
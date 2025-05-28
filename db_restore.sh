#!/bin/bash

# Usage: ./restore_from_drive.sh <db_name> <db_user> <db_password>
DOCKER_SERVICE_NAME="db"
DOCKER_DB_NAME="$1"
DOCKER_DB_USER="$2"
DOCKER_DB_PASSWORD="$3"

if [ -z "$3" ]; then
  echo "Usage: $0 <db_name> <db_user> <db_password>"
  exit 1
fi

# === CONFIGURATION ===
FILEID="1FDU5Wm8mHCBxlTMD-CptyyTqdSDkjfH5"
DUMP_URL="https://drive.usercontent.google.com/download?id=${FILEID}&confirm=t"
BACKUP_FILE_LOCAL="db/full_restore.dump"
BACKUP_FILE_IN_CONTAINER="/tmp/full_restore.dump"

# === Step 1: Download the dump using curl or wget ===
mkdir -p db

echo "⬇️ Downloading dump from $DUMP_URL..."
if command -v curl > /dev/null; then
  wget --no-check-certificate "$DUMP_URL" -O "$BACKUP_FILE_LOCAL"
else
    echo "❌ wget is available. Cannot download."
    exit 1
fi

if [ $? -ne 0 ] || [ ! -f "$BACKUP_FILE_LOCAL" ]; then
    echo "❌ Failed to download dump file."
    exit 1
fi
echo "✅ Dump file downloaded to $BACKUP_FILE_LOCAL"

# === Step 2: Find container and copy the dump ===
DOCKER_CONTAINER_NAME=$(docker compose ps -q "$DOCKER_SERVICE_NAME")
if [ -z "$DOCKER_CONTAINER_NAME" ]; then
    echo "❌ Docker container for service '$DOCKER_SERVICE_NAME' not found."
    exit 1
fi

echo "📦 Copying dump file into container..."
docker cp "$BACKUP_FILE_LOCAL" "$DOCKER_CONTAINER_NAME:$BACKUP_FILE_IN_CONTAINER"

# === Step 3: Restore the dump ===
echo "🛠 Restoring database from dump..."
docker exec -e PGPASSWORD="$DOCKER_DB_PASSWORD" "$DOCKER_CONTAINER_NAME" \
    pg_restore -U "$DOCKER_DB_USER" -d "$DOCKER_DB_NAME" "$BACKUP_FILE_IN_CONTAINER"

if [ $? -ne 0 ]; then
    echo "❌ Restore failed."
    exit 1
fi

echo "✅ Restore completed successfully."

# === Step 4: Cleanup ===
echo "🧹 Cleaning up..."
rm -f "$BACKUP_FILE_LOCAL"
docker exec "$DOCKER_CONTAINER_NAME" rm -f "$BACKUP_FILE_IN_CONTAINER"
echo "✅ Cleanup done."

#!/bin/bash
# Initialize database with historical data if it doesn't exist

DB_PATH="${DATABASE_PATH:-/home/orbcomm/.orbcomm/tracker.db}"
DB_DIR=$(dirname "$DB_PATH")

# Create directory if it doesn't exist
mkdir -p "$DB_DIR"

# If database doesn't exist, load from backup
if [ ! -f "$DB_PATH" ]; then
    echo "Loading historical database from backup..."
    sqlite3 "$DB_PATH" < /app/database_backup.sql
    echo "Database initialized with historical data"
else
    echo "Database already exists, skipping initialization"
fi

#!/bin/bash

echo "🚀 Starting Rezzy Backend..."

# Check if migration script exists
if [ -f "simple_migrate.py" ]; then
    echo "📊 Running database migration..."
    python simple_migrate.py
    echo "✅ Migration process completed"
elif [ -f "migrate_database.py" ]; then
    echo "📊 Running database migration..."
    python migrate_database.py
    echo "✅ Migration process completed"
else
    echo "⚠️ Migration script not found, skipping..."
fi

# Start the application
echo "🌐 Starting FastAPI application..."
exec uvicorn app:app --host 0.0.0.0 --port $PORT 
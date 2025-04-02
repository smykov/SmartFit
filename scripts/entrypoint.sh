#!/bin/bash
set -e

# Настройка прав на выполнение
chmod +x scripts/*.py
chmod +x scripts/*.sh

# Заполнение базы начальными данными (если указан флаг)
if [ "$SEED_DATABASE" = "true" ]; then
    echo "Seeding database with initial data..."
    python scripts/seed_database.py
fi

# Запуск сервера
if [ "$DEBUG" = "true" ]; then
    echo "Starting server in development mode..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting server in production mode..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
fi

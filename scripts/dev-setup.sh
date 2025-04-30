#!/bin/bash

# Установка pre-commit hooks
pip install pre-commit
pre-commit install

# Создание локального .env файла
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update with your credentials."
fi

# Запуск локальной версии с помощью docker-compose
docker-compose -f docker-compose.dev.yml up -d

# Установка зависимостей для разработки
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "Development environment is ready!"
echo "API running at: http://localhost:8000"
echo "Grafana running at: http://localhost:3000"
echo "Prometheus running at: http://localhost:9090"
#!/bin/bash

# Запуск всех тестов
run_all() {
    docker-compose -f docker-compose-tests.yml up --build tests
}

# Запуск только модульных тестов
run_unit() {
    docker-compose -f docker-compose-tests.yml run --rm tests pytest -xvs tests/unit
}

# Запуск только интеграционных тестов
run_integration() {
    docker-compose -f docker-compose-tests.yml run --rm tests pytest -xvs tests/integration
}

# Запуск только функциональных тестов
run_functional() {
    docker-compose -f docker-compose-tests.yml run --rm tests pytest -xvs tests/functional
}

# Запуск тестов с измерением покрытия
run_coverage() {
    docker-compose -f docker-compose-tests.yml run --rm tests pytest --cov=app --cov-report=term --cov-report=html
}

# Запуск конкретного теста
run_specific() {
    if [ -z "$1" ]; then
        echo "Укажите путь к тестовому файлу"
        exit 1
    fi
    docker-compose -f docker-compose-tests.yml run --rm tests pytest -xvs "$1"
}

case "$1" in
    unit)
        run_unit
        ;;
    integration)
        run_integration
        ;;
    functional)
        run_functional
        ;;
    coverage)
        run_coverage
        ;;
    specific)
        run_specific "$2"
        ;;
    *)
        run_all
        ;;
esac
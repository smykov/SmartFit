#!/usr/bin/env python3
import os
import sys
import asyncio
import logging

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.seed_data import DataSeeder

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

async def main():
    """Точка входа для скрипта заполнения базы данных"""
    try:
        logger.info("Starting database seeding script")
        
        # Запускаем заполнение данных
        success = await DataSeeder.seed_all()
        
        if success:
            logger.info("Database seeding completed successfully")
        else:
            logger.error("Database seeding failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during database seeding: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import logging
from pathlib import Path

from app.db.firebase import firebase_client

logger = logging.getLogger(__name__)

class DataSeeder:
    """Класс для заполнения базы данных начальными данными"""
    
    @staticmethod
    async def seed_products():
        """Загружает данные о продуктах из JSON-файла"""
        try:
            # Путь к файлу с продуктами
            products_file = Path(__file__).resolve().parents[2] / "data" / "guatemala_products.json"
            
            if not products_file.exists():
                logger.error(f"Products file not found: {products_file}")
                return False
            
            # Загружаем данные из файла
            with open(products_file, "r", encoding="utf-8") as file:
                products = json.load(file)
            
            logger.info(f"Loaded {len(products)} products from file")
            
            # Загружаем в базу данных
            products_loaded = 0
            for product in products:
                # Проверяем, существует ли уже продукт с таким именем
                existing_products = firebase_client.query_documents(
                    "products", "name", "==", product["name"]
                )
                
                if existing_products:
                    # Если продукт уже существует, пропускаем его
                    logger.debug(f"Product {product['name']} already exists, skipping")
                    continue
                
                # Добавляем новый продукт
                product_id = firebase_client.add_document("products", product)
                
                if product_id:
                    products_loaded += 1
                    logger.debug(f"Added product: {product['name']} with ID: {product_id}")
                else:
                    logger.error(f"Failed to add product: {product['name']}")
            
            logger.info(f"Successfully loaded {products_loaded} new products")
            return True
            
        except Exception as e:
            logger.error(f"Error seeding products: {str(e)}")
            return False
    
    @staticmethod
    async def create_demo_user():
        """Создает демо-пользователя для тестирования"""
        try:
            # Проверяем, существует ли уже демо-пользователь
            demo_users = firebase_client.query_documents(
                "users", "phone_number", "==", "+50212345678"
            )
            
            if demo_users:
                logger.info("Demo user already exists, skipping creation")
                return demo_users[0]
            
            # Создаем демо-пользователя
            demo_user = {
                "phone_number": "+50212345678",
                "name": "Demo User",
                "email": "demo@guatefit.com",
                "gender": "male",
                "age": 30,
                "height": 175.0,
                "current_weight": 85.0,
                "target_weight": 75.0,
                "activity_level": "moderate",
                "weight_goal": "lose",
                "diet_preference": "regular",
                "budget_limit": 400.0,
                "allergies": [],
                "disliked_products": [],
                "local_cuisine_preference": True,
                "is_onboarding_completed": True,
                "is_active": True,
                "weight_history": {
                    "2024-01-01": 85.0,
                    "2024-01-05": 84.5,
                    "2024-01-10": 84.0,
                    "2024-01-15": 83.2,
                    "2024-01-20": 82.7,
                    "2024-01-25": 82.1,
                    "2024-01-30": 81.5
                },
                "water_intake_history": {
                    "2024-01-01": 1500,
                    "2024-01-02": 1800,
                    "2024-01-03": 2000,
                    "2024-01-04": 1700,
                    "2024-01-05": 2200
                },
                "registration_source": "demo"
            }
            
            # Добавляем пользователя
            user_id = firebase_client.add_document("users", demo_user)
            
            if user_id:
                logger.info(f"Created demo user with ID: {user_id}")
                demo_user["id"] = user_id
                return demo_user
            else:
                logger.error("Failed to create demo user")
                return None
            
        except Exception as e:
            logger.error(f"Error creating demo user: {str(e)}")
            return None
    
    @staticmethod
    async def seed_all():
        """Запускает полное заполнение базы начальными данными"""
        try:
            logger.info("Starting database seeding")
            
            # Последовательно выполняем все задачи
            await DataSeeder.seed_products()
            await DataSeeder.create_demo_user()
            
            logger.info("Database seeding completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during database seeding: {str(e)}")
            return False

# Функция для запуска заполнения данных из командной строки
async def main():
    """Точка входа для запуска заполнения данных"""
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Запускаем заполнение данных
    await DataSeeder.seed_all()

if __name__ == "__main__":
    asyncio.run(main())

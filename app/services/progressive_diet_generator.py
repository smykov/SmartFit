import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import pytz

from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.templates.prompts import create_full_diet_system_prompt, create_full_diet_user_prompt, \
    create_single_day_user_prompt
from config import settings

logger = logging.getLogger(__name__)


class ProgressiveDietGenerator:
    """
    Класс для поэтапной генерации полного плана диеты по дням недели
    с сохранением промежуточных результатов
    """

    DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    MAX_RETRIES = 3

    def __init__(
            self,
            llm_service,
            diet_plan_repository: IDietPlanRepository,
            short_plan_id: str,
            user_data: Dict[str, Any],
            full_plan_id: Optional[str] = None
    ):
        """
        Инициализация генератора

        Args:
            llm_service: Сервис для взаимодействия с LLM моделью
            diet_plan_repository: Репозиторий для работы с планами диет
            short_plan_id: ID краткого плана в базе данных
            user_data: Данные пользователя для персонализации плана
        """
        self.llm_service = llm_service
        self.diet_plan_repository = diet_plan_repository
        self.short_plan_id = short_plan_id
        self.user_data = user_data
        self.full_plan_id = full_plan_id
        self.system_prompt = create_full_diet_system_prompt()

    async def generate_full_plan(self) -> Optional[Dict[str, Any]]:
        """
        Запускает процесс поэтапной генерации полного плана диеты

        Returns:
            Optional[Dict[str, Any]]: Полный план диеты или None в случае ошибки
        """
        try:
            # Получаем краткий план из БД
            short_plan = await self.diet_plan_repository.get_by_id(self.short_plan_id)
            if not short_plan:
                logger.error(f"Short plan {self.short_plan_id} not found")
                return None

            # Если у нас есть ID существующего плана, получаем его из БД
            full_plan = None
            if self.full_plan_id:
                full_plan = await self.diet_plan_repository.get_by_id(self.full_plan_id)
                if not full_plan:
                    logger.error(f"Full plan {self.full_plan_id} not found, will create a new one")
                    self.full_plan_id = None
                elif full_plan.get("status") != "in_progress":
                    logger.warning(
                        f"Full plan {self.full_plan_id} is not in 'in_progress' status: {full_plan.get('status')}"
                    )
                    # Если план не в статусе in_progress, создадим новый
                    self.full_plan_id = None
                    full_plan = None

            # Если у нас нет существующего плана, создаем новый
            if not full_plan:
                # Создаем базовую структуру полного плана
                full_plan = self._initialize_full_plan(short_plan)

                # Сохраняем базовую структуру в БД для отслеживания прогресса
                self.full_plan_id = await self.diet_plan_repository.create(full_plan)
                if not self.full_plan_id:
                    logger.error("Failed to save initial full diet plan to database")
                    return None

                full_plan["id"] = self.full_plan_id

            # Определяем, какие дни уже сгенерированы
            generated_days = set()
            if "daily_plans" in full_plan and full_plan["daily_plans"]:
                generated_days = set(full_plan["daily_plans"].keys())
                logger.info(f"Found already generated days: {', '.join(generated_days)}")

            # Генерируем план для каждого недостающего дня недели
            for day_of_week in self.DAYS_OF_WEEK:
                # Пропускаем уже сгенерированные дни
                if day_of_week in generated_days:
                    logger.info(f"Skipping already generated day: {day_of_week}")
                    continue

                logger.info(f"Generating plan for day: {day_of_week}")
                day_plan = await self._generate_day_plan(day_of_week, short_plan)

                if day_plan:
                    # Обновляем план в базе данных
                    full_plan["daily_plans"][day_of_week] = day_plan
                    await self.diet_plan_repository.update_daily_plan(
                        self.full_plan_id,
                        day_of_week,
                        day_plan
                    )
                    logger.info(f"Successfully generated plan for {day_of_week}")
                else:
                    logger.error(f"Failed to generate plan for {day_of_week}")

            # Проверяем, все ли дни недели успешно сгенерированы
            if all(day in full_plan["daily_plans"] for day in self.DAYS_OF_WEEK):
                # Обновляем статус плана на "active"
                await self.diet_plan_repository.update(
                    self.full_plan_id,
                    {"status": "active", "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()}
                )
                logger.info(f"Full plan generation completed successfully")
            else:
                # Если не все дни сгенерированы, оставляем статус "in_progress"
                missing_days = [day for day in self.DAYS_OF_WEEK if day not in full_plan["daily_plans"]]
                logger.warning(f"Full plan generation incomplete. Missing days: {missing_days}")

            return full_plan

        except Exception as e:
            logger.error(f"Error in progressive diet generation: {str(e)}")
            return None

    async def _generate_day_plan(self, day_of_week: str, short_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Генерирует детальный план для конкретного дня недели

        Args:
            day_of_week: День недели (monday, tuesday, etc.)
            short_plan: Краткий план диеты

        Returns:
            Optional[Dict[str, Any]]: План на день или None в случае ошибки
        """
        retries = 0

        while retries < self.MAX_RETRIES:
            try:
                user_prompt = create_full_diet_user_prompt(self.user_data, short_plan)
                extra_prompt_for_single_day = create_single_day_user_prompt(day_of_week)

                # Вызываем LLM для генерации плана на день
                response = await self.llm_service.generate_completion(
                    self.system_prompt,
                    extra_prompt_for_single_day,
                    [
                        {"role": "user", "content": user_prompt},
                    ]
                )

                # Пытаемся распарсить ответ
                try:
                    day_plan = json.loads(response)

                    # Проверяем наличие необходимых полей
                    if self._validate_day_plan(day_plan):
                        return day_plan
                    else:
                        logger.error(f"Invalid day plan structure for {day_of_week}")
                        retries += 1

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response for {day_of_week}: {response[:100]}...")
                    retries += 1

                # Добавляем экспоненциальную задержку между попытками
                await asyncio.sleep(2 ** retries)

            except Exception as e:
                logger.error(f"Error generating day plan for {day_of_week}: {str(e)}")
                retries += 1

        logger.error(f"Failed to generate day plan for {day_of_week} after {self.MAX_RETRIES} attempts")
        return None

    def _initialize_full_plan(self, short_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Инициализирует структуру полного плана на основе краткого плана

        Args:
            short_plan: Краткий план диеты

        Returns:
            Dict[str, Any]: Базовая структура полного плана
        """
        # Копируем общие поля из краткого плана
        full_plan = {
            "user_id": short_plan.get("user_id"),
            "short_plan_id": self.short_plan_id,
            "personalized_note": short_plan.get("personalized_note", ""),
            "general_recommendations": short_plan.get("general_recommendations", ""),
            "caloric_deficit": short_plan.get("caloric_deficit"),
            "caloric_proficit": short_plan.get("caloric_proficit"),
            "version": "full",
            "status": "in_progress",  # Промежуточный статус для отслеживания прогресса
            "daily_plans": {},  # Будет заполняться постепенно
            "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
            "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
        }

        return full_plan

    def _validate_day_plan(self, day_plan: Dict[str, Any]) -> bool:
        """
        Проверяет структуру плана на день

        Args:
            day_plan: План на день

        Returns:
            bool: True, если план валидный
        """
        # Проверяем наличие обязательных полей
        if not isinstance(day_plan, dict):
            return False

        if "meals" not in day_plan or not isinstance(day_plan["meals"], list):
            return False

        # Проверяем структуру каждого приема пищи
        for meal in day_plan["meals"]:
            if not isinstance(meal, dict):
                return False

            required_fields = ["type", "title", "products", "calories", "proteins", "fats", "carbs"]
            if not all(field in meal for field in required_fields):
                return False

        return True

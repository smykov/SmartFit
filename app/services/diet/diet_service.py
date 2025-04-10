# app/services/diet/diet_service.py
import asyncio
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from app.db.interfaces.user_repository_interface import IUserRepository
from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.db.interfaces.product_repository_interface import IProductRepository
from app.db.interfaces.shopping_list_repository_interface import IShoppingListRepository

from app.localization.messages import DietMessages
from app.services.diet.base_service import BaseDietService
from app.services.formatter.diet_formatter_service import DietFormatterService
from app.services.diet.diet_plan_manager import DietPlanManager
from app.services.diet.diet_service_interface import IDietService
from app.services.diet.shopping_list_manager import ShoppingListManager
from app.services.llm import llm_service
from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.message_interface import IMessageService


class DietService(BaseDietService, IDietService):
    """Основной сервис для работы с диетами, использующий специализированные компоненты"""

    def __init__(
            self,
            user_repository: IUserRepository,
            message_service: IMessageService,
            localization_service: ILocalizationService,
            diet_plan_repository: IDietPlanRepository,
            product_repository: IProductRepository,
            shopping_list_repository: IShoppingListRepository
    ):
        """Инициализация сервиса диет с необходимыми компонентами"""
        super().__init__()
        # Инициализируем компоненты с новыми репозиториями
        self.diet_plan_manager = DietPlanManager(
            llm_service,
            diet_plan_repository,
            product_repository,
            user_repository
        )
        self.shopping_list_manager = ShoppingListManager(
            llm_service,
            diet_plan_repository,
            shopping_list_repository
        )
        self.formatter = DietFormatterService(localization_service)
        self.localization_service = localization_service
        self.messages = DietMessages()
        self.message_service = message_service
        self.llm_service = llm_service
        self.user_repository = user_repository
        self.diet_plan_repository = diet_plan_repository
        self.product_repository = product_repository
        self.shopping_list_repository = shopping_list_repository

    async def start_full_diet_generation(self, user_id: str, short_plan_id: str) -> bool:
        """
        Запускает фоновую генерацию полного плана диеты и отправляет уведомление пользователю

        Args:
            user_id: ID пользователя
            short_plan_id: ID краткой версии плана диеты

        Returns:
            bool: Успешность запуска генерации
        """
        try:
            # Получаем данные пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                self.logger.error(f"Пользователь с ID {user_id} не найден")
                return False

            # Запускаем задачу генерации полного плана в фоновом режиме
            asyncio.create_task(self._generate_full_diet_plan_task(user_id, short_plan_id))

            return True
        except Exception as e:
            self.logger.error(f"Ошибка при запуске генерации полного плана: {str(e)}")
            return False

    async def _generate_full_diet_plan_task(self, user_id: str, short_plan_id: str):
        """
        Фоновая задача для генерации полного плана диеты

        Args:
            user_id: ID пользователя
            short_plan_id: ID краткой версии плана диеты
        """
        try:
            # Получаем данные пользователя для отправки уведомлений
            user = await self.user_repository.get_by_id(user_id)
            phone_number = user.get("phone_number")
            lang = user.get("language")

            # Генерируем полный план
            full_plan = await self.generate_full_diet_plan(short_plan_id)

            if full_plan and "error" not in full_plan:
                # Отправляем уведомление пользователю
                await self.message_service.send_template_message(
                    phone_number,
                    "diet.full.created",
                    user_id
                )

                # Отправляем сводку плана
                diet_summary = self.get_diet_summary(full_plan, lang)
                await self.message_service.send_message(phone_number, diet_summary)
                commands_message = self.get_diet_summary_commands(full_plan, lang)
                await self.message_service.send_message(phone_number, commands_message)
            else:
                # В случае ошибки
                await self.message_service.send_template_message(
                    phone_number,
                    "diet.full.creating_error",
                    user_id
                )

        except Exception as e:
            self.logger.error(f"Ошибка в задаче генерации полного плана: {str(e)}")

    async def generate_full_diet_plan(self, short_plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует полную версию плана диеты на основе краткого плана

        Args:
            short_plan_id: ID краткого плана диеты

        Returns:
            Optional[Dict[str, Any]]: Полный план диеты или None в случае ошибки
        """
        try:
            # Получаем краткий план диеты
            short_plan = await self.diet_plan_manager.get_diet_plan_by_id(short_plan_id)

            if not short_plan:
                self.logger.error(f"Краткий план с ID {short_plan_id} не найден")
                return None

            # Получаем данные пользователя
            user_id = short_plan.get("user_id")
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                self.logger.error(f"Пользователь с ID {user_id} не найден")
                return None

            # Используем прогрессивный генератор диет для создания полного плана
            from app.services.progressive_diet_generator import ProgressiveDietGenerator

            generator = ProgressiveDietGenerator(self.llm_service, short_plan_id, user)
            full_plan = await generator.generate_full_plan()

            if not full_plan:
                self.logger.error(f"Не удалось создать полный план диеты для плана {short_plan_id}")
                return None

            return full_plan

        except Exception as e:
            self.logger.error(f"Ошибка при генерации полного плана диеты: {str(e)}")
            return None

    async def answer_nutrition_question(self, user_id: str, question: str) -> str:
        """
        Отвечает на вопрос пользователя о питании

        Args:
            user_id: ID пользователя
            question: Вопрос о питании

        Returns:
            str: Ответ на вопрос
        """
        try:
            # Получаем данные пользователя для контекста
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                return "Извините, не удалось найти информацию о пользователе."

            # Отправляем запрос к LLM сервису
            response = await self.llm_service.answer_nutrition_question(user_id, question)

            return response

        except Exception as e:
            self.logger.error(f"Ошибка при ответе на вопрос о питании: {str(e)}")
            return "Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте позже."

    # Методы делегирования для DietPlanManager
    async def generate_short_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует краткую версию плана диеты

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Краткий план диеты
        """
        return await self.diet_plan_manager.generate_short_diet_plan(user_id)

    async def approve_short_diet_plan(self, plan_id: str) -> bool:
        """
        Отмечает краткий план диеты как согласованный

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат операции
        """
        return await self.diet_plan_manager.approve_short_diet_plan(plan_id)

    async def update_short_diet_plan(self, plan_id: str, updated_days: Dict[str, Any], comment: str = None) -> Tuple[
        bool, Dict[str, Any]]:
        """
        Обновляет краткую версию плана питания

        Args:
            plan_id: ID плана диеты
            updated_days: Словарь {день_недели: данные_на_день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        return await self.diet_plan_manager.update_short_diet_plan(plan_id, updated_days, comment)

    async def update_diet_plan_partially(self, diet_plan_id: str, updated_days: Dict[str, Any], comment: str = None) -> \
            Tuple[bool, Dict[str, Any]]:
        """
        Обновляет частично план питания

        Args:
            diet_plan_id: ID плана диеты
            updated_days: Словарь {дата: данные на день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        return await self.diet_plan_manager.update_diet_plan_partially(diet_plan_id, updated_days, comment)

    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты
        """
        return await self.diet_plan_manager.get_current_diet(user_id)

    async def get_diet_for_day(self, user_id: str, day_date: date) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день

        Args:
            user_id: ID пользователя
            day_date: Дата, на которую нужен план

        Returns:
            Optional[Dict[str, Any]]: План на день
        """
        return await self.diet_plan_manager.get_diet_for_day(user_id, day_date)

    async def get_today_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на сегодняшний день

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План на сегодня
        """
        return await self.diet_plan_manager.get_today_diet(user_id)

    async def get_diet_for_weekday(self, user_id: str, weekday: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день недели

        Args:
            user_id: ID пользователя
            weekday: День недели ('monday', 'tuesday', и т.д.)

        Returns:
            Optional[Dict[str, Any]]: План на день
        """
        return await self.diet_plan_manager.get_diet_for_weekday(user_id, weekday)

    async def update_diet_plan(self, diet_plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет план диеты на основе запроса пользователя

        Args:
            diet_plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        return await self.diet_plan_manager.update_diet_plan(diet_plan_id, update_request)

    async def update_short_diet_plan_by_request(self, plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет краткий план диеты на основе запроса пользователя

        Args:
            plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        return await self.diet_plan_manager.update_short_diet_plan_by_request(plan_id, update_request)

    # Методы делегирования для ShoppingListManager
    async def generate_shopping_list(self, diet_plan_id: str) -> Dict[str, Any]:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            Dict[str, Any]: Список покупок
        """
        return await self.shopping_list_manager.generate_shopping_list(diet_plan_id)

    async def mark_product_as_purchased(self, user_id: str, product_name: str) -> Dict[str, Any]:
        """
        Отмечает продукт как купленный в списке покупок

        Args:
            user_id: ID пользователя
            product_name: Название продукта

        Returns:
            Dict[str, Any]: Результат операции
        """
        return await self.shopping_list_manager.mark_product_as_purchased(user_id, product_name)

    # Методы делегирования для DietFormatter
    def get_diet_summary(self, diet_plan: Dict[str, Any], lang: str) -> str:
        """
        Создает сводку плана диеты и сообщение с командами

        Args:
            diet_plan: План диеты
            lang: Код языка (по умолчанию используется системный язык)

        Returns:
            Tuple[str, str]: (сводка плана, команды для взаимодействия)
        """
        return self.formatter.get_diet_summary(diet_plan, lang)

    def get_diet_summary_commands(self, diet_plan: Dict[str, Any], lang: str) -> str:
        """
        Создает сводку плана диеты и сообщение с командами

        Args:
            diet_plan: План диеты
            lang: Код языка (по умолчанию используется системный язык)

        Returns:
            Tuple[str, str]: (сводка плана, команды для взаимодействия)
        """
        return self.formatter.get_diet_summary_commands(diet_plan, lang)

    def get_full_diet_plan(self, diet_plan: Dict[str, Any]) -> List[str]:
        """
        Создает полный план диеты на все дни

        Args:
            diet_plan: План диеты

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        return self.formatter.get_full_diet_plan(diet_plan)

    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: date = None,
                          lang: Optional[str] = None) -> List[str]:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план
            lang: Код языка

        Returns:
            List[str]: Сообщения с планом на день
        """
        return self.formatter.get_day_diet_plan(diet_plan, day_date, lang)

    def get_diet_tracking_info_message(self, lang: Optional[str] = None) -> str:
        """
        Создает сообщение с информацией о командах трекинга диеты

        Args:
            lang: Код языка

        Returns:
            str: Сообщение с информацией по трекингу
        """
        return self.formatter.get_diet_tracking_info_message(lang)

    def format_shopping_list(self, shopping_list_data: Dict[str, Any]) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            str: Отформатированный список покупок
        """
        return self.formatter.format_shopping_list(shopping_list_data)

    async def get_pending_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты, ожидающий согласования пользователем

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План диеты или None, если такого плана нет
        """
        try:
            # Делегируем запрос менеджеру планов диет
            return await self.diet_plan_manager.get_pending_diet_plan(user_id)
        except Exception as e:
            self.logger.error(f"Ошибка при получении ожидающего плана диеты: {str(e)}")
            return None

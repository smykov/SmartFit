# app/services/recovery/diet_recovery_service.py
import logging
from typing import Dict, Any, List, Optional

from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.diet.diet_service_interface import IDietService
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.services.progressive_diet_generator import ProgressiveDietGenerator


class DietRecoveryService:
    """
    Сервис для восстановления прерванных процессов генерации диетических планов
    """

    def __init__(
            self,
            diet_plan_repository: IDietPlanRepository,
            user_repository: IUserRepository,
            diet_service: IDietService,
            messenger_service: IMessengerService,
            llm_service
    ):
        self.diet_plan_repository = diet_plan_repository
        self.user_repository = user_repository
        self.diet_service = diet_service
        self.messenger_service = messenger_service
        self.llm_service = llm_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def recover_plans_in_progress(self) -> int:
        """
        Восстанавливает генерацию диетических планов, которые были прерваны

        Returns:
            int: Количество восстановленных планов
        """
        try:
            # Получаем все планы в статусе IN_PROGRESS
            in_progress_plans = await self.diet_plan_repository.find_by_status("in_progress")
            self.logger.info(f"Found {len(in_progress_plans)} diet plans in status 'in_progress'")

            # Счетчик восстановленных планов
            recovered_count = 0

            for plan in in_progress_plans:
                user_id = plan.get("user_id")
                plan_id = plan.get("id")

                if not user_id or not plan_id:
                    self.logger.warning(f"Skipping plan with missing user_id or plan_id: {plan}")
                    continue

                # Проверяем версию плана
                version = plan.get("version")
                if version == "full":
                    # Находим соответствующий короткий план для этого пользователя
                    short_plans = await self.diet_plan_repository.get_user_plans(user_id)
                    short_plan = next(
                        (p for p in short_plans if p.get("version") == "short" and p.get("status") == "approved"),
                        None
                    )

                    if short_plan:
                        short_plan_id = short_plan.get("id")
                        self.logger.info(f"Found approved short plan {short_plan_id} for user {user_id}")

                        # Получаем данные пользователя
                        user = await self.user_repository.get_by_id(user_id)
                        if not user:
                            self.logger.error(f"User {user_id} not found")
                            continue

                        # Возобновляем генерацию плана через ProgressiveDietGenerator
                        success = await self.resume_diet_generation(
                            user_id,
                            short_plan_id,
                            plan_id,
                            user
                        )

                        if success:
                            recovered_count += 1

                            # Уведомляем пользователя
                            await self.notify_user(user_id)
                    else:
                        self.logger.warning(f"No approved short plan found for user {user_id}")

            self.logger.info(f"Successfully recovered {recovered_count} diet plans")
            return recovered_count

        except Exception as e:
            self.logger.error(f"Error recovering diet plans in progress: {str(e)}")
            return 0

    async def resume_diet_generation(self, user_id: str, short_plan_id: str, full_plan_id: str,
                                     user_data: Dict[str, Any]) -> bool:
        """
        Возобновляет процесс генерации полного плана диеты

        Args:
            user_id: ID пользователя
            short_plan_id: ID короткого плана
            full_plan_id: ID полного плана, который нужно восстановить
            user_data: Данные пользователя

        Returns:
            bool: Успешность возобновления
        """
        try:
            # Создаем экземпляр ProgressiveDietGenerator с существующим full_plan_id
            generator = ProgressiveDietGenerator(
                llm_service=self.llm_service,
                diet_plan_repository=self.diet_plan_repository,
                short_plan_id=short_plan_id,
                user_data=user_data,
                full_plan_id=full_plan_id  # Передаем существующий ID
            )

            # Запускаем генерацию в фоновом режиме
            from asyncio import create_task
            create_task(self._generate_plan_async(generator, user_id))

            return True

        except Exception as e:
            self.logger.error(f"Error resuming diet generation: {str(e)}")
            return False

    async def _generate_plan_async(self, generator: ProgressiveDietGenerator, user_id: str):
        """
        Асинхронная задача для генерации плана

        Args:
            generator: Экземпляр ProgressiveDietGenerator
            user_id: ID пользователя
        """
        try:
            # Генерируем план
            result = await generator.generate_full_plan()

            if not result:
                self.logger.error(f"Failed to generate full plan for user {user_id}")
                return

            # Генерация успешна, получаем пользователя и отправляем уведомление
            user = await self.user_repository.get_by_id(user_id)
            full_plan_id = generator.full_plan_id

            if not user:
                self.logger.error(f"User {user_id} not found after plan generation")
                return

            # Получаем язык пользователя
            lang = await self.diet_service.localization_service.get_user_language(user_id)

            # Получаем сообщения для отправки
            full_plan = await self.diet_plan_repository.get_by_id(full_plan_id)

            if full_plan and full_plan.get("status") == "active":
                # Если план успешно сгенерирован, отправляем уведомление
                summary_message = self.diet_service.get_diet_summary(full_plan, lang)
                # tracking_info_message = self.diet_service.get_diet_tracking_info_message(lang)

                # Отправляем сообщения пользователю
                await self.messenger_service.send_message(
                    user.get("phone_number"),
                    self.diet_service.localization_service.get_message("diet.full.created", lang),
                    {"user_id": user_id}
                )

                await self.messenger_service.send_message(
                    user.get("phone_number"),
                    summary_message,
                    {"user_id": user_id}
                )

                # await self.messenger_service.send_message(
                #     user.get("phone_number"),
                #     tracking_info_message,
                #     {"user_id": user_id}
                # )

        except Exception as e:
            self.logger.error(f"Error in async generation for user {user_id}: {str(e)}")

    async def notify_user(self, user_id: str) -> bool:
        """
        Уведомляет пользователя о возобновлении генерации плана

        Args:
            user_id: ID пользователя

        Returns:
            bool: Успешность отправки уведомления
        """
        try:
            # Получаем пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                self.logger.error(f"User {user_id} not found")
                return False

            phone_number = user.get("phone_number")
            if not phone_number:
                self.logger.error(f"User {user_id} has no phone number")
                return False

            # Отправляем сообщение
            message = "Извините за задержку. Мы продолжаем генерацию вашего плана питания. Он будет готов в ближайшее время."
            await self.messenger_service.send_message(
                phone_number,
                message,
                {"user_id": user_id}
            )

            return True

        except Exception as e:
            self.logger.error(f"Error notifying user {user_id}: {str(e)}")
            return False
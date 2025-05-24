# app/services/commands/commands/diet_approval_command.py
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Type, Pattern
import re

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand
from config import settings


class DietApprovalCommand(BaseCommand):
    """
    Команда для согласования или отклонения плана питания
    """

    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализация команды с зависимостями

        Args:
            dependencies: Словарь зависимостей для команды
        """
        super().__init__(dependencies)

        # Регулярные выражения для определения ответа пользователя
        self.approval_patterns: Dict[str, Pattern] = {
            "approve": re.compile(r'^(согласен|согласна|подтверждаю|ок|да|хорошо|все ок|yes|ok)$', re.IGNORECASE),
            "disapprove": re.compile(r'^(не согласен|не согласна|не подтверждаю|нет|не ок|не хорошо|no|отклоняю)$',
                                     re.IGNORECASE),
        }

    async def can_execute(self, user_id: str) -> bool:
        """
        Проверяет возможность выполнения команды согласования плана диеты

        Args:
            user_id: ID пользователя

        Returns:
            bool: Возможность выполнения команды
        """
        try:
            # Проверяем наличие ожидающего согласования плана
            pending_plan = await self._get_pending_diet_plan(user_id)
            return pending_plan is not None
        except Exception as e:
            self.logger.error(f"Error checking diet approval prerequisites: {str(e)}")
            return False

    async def _get_pending_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты, ожидающий согласования

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План диеты или None
        """
        return await self.diet_service.get_pending_diet_plan(user_id)

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды согласования плана диеты

        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит текст сообщения)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)

        try:
            # Получаем данные о пользователе
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.User.NOT_FOUND, lang)
                }

            # Получаем последний несогласованный план
            pending_plan = await self._get_pending_diet_plan(user_id)

            if not pending_plan:
                # Используем локализованное сообщение
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Messaging.NO_PENDING_PLAN, lang)
                }

            # Получаем текст сообщения из параметров
            if not params or "approval_text" not in params:
                # Пытаемся получить текст из других возможных мест в параметрах
                approval_text = None
                if "params" in params:
                    if isinstance(params["params"], tuple) and len(params["params"]) > 0:
                        approval_text = params["params"][0]
                    elif isinstance(params["params"], dict) and "approval_text" in params["params"]:
                        approval_text = params["params"]["approval_text"]

                if not approval_text:
                    self.logger.error("Approval text not found in parameters")
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Messaging.INVALID_MESSAGE_FORMAT, lang)
                    }
            else:
                approval_text = params["approval_text"]

            # Определяем тип ответа (согласие или отказ)
            is_approved = bool(self.approval_patterns["approve"].match(approval_text))
            recipient_id = user.get("phone_number", "")

            if is_approved:
                # Согласуем план
                success = await self.diet_service.approve_short_diet_plan(pending_plan["id"])

                if success:
                    # Обновляем контекст пользователя
                    await self.user_repository.update(user_id, {
                        "last_conversation_context": {
                            "last_action": "plan_approved",
                            "timestamp": DateHelper.get_current_datetime().isoformat(),
                            "plan_id": pending_plan["id"]
                        }
                    })

                    # Отправляем сообщение о успешном согласовании
                    await self.messenger_service.send_template_message(
                        recipient_id,
                        LK.Diet.Short.APPROVAL_SUCCESS,
                        user_id
                    )

                    # Запускаем генерацию полного плана
                    await self.diet_service.start_full_diet_generation(user_id, pending_plan["id"])

                    return {
                        "success": True,
                        "action": "plan_approved",
                        "message": self.get_localized_message(LK.Diet.Short.APPROVAL_SUCCESS, lang)
                    }
                else:
                    return {
                        "success": False,
                        "action": "approval_failed",
                        "message": self.get_localized_message(LK.Diet.Short.APPROVAL_ERROR, lang)
                    }
            else:
                # Отклонение плана - генерируем новый краткий план
                await self.messenger_service.send_template_message(
                    recipient_id,
                    LK.Diet.Short.DISAPPROVAL,
                    user_id
                )

                # Обновляем контекст пользователя
                await self.user_repository.update(user_id, {
                    "last_conversation_context": {
                        "last_action": "plan_disapproved",
                        "timestamp": DateHelper.get_current_datetime().isoformat(),
                        "plan_id": pending_plan["id"]
                    }
                })

                return {
                    "success": True,
                    "action": "plan_disapproved",
                    "message": self.get_localized_message(LK.Diet.Short.DISAPPROVAL, lang)
                }

        except Exception as e:
            self.logger.error(f"Error executing diet approval command: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Diet.Short.APPROVAL_ERROR, lang)
            }

    def get_error_message(self, lang: str = None) -> str:
        """
        Получение сообщения об ошибке

        Args:
            lang: Язык пользователя

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Messaging.NO_PENDING_PLAN, lang)
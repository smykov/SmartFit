# app/services/onboarding/onboarding_service.py
import logging
from typing import Dict, Any, Optional, Tuple

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.commands.interfaces.command_handler_interface import ICommandHandler
from app.services.diet.diet_service_interface import IDietService
from app.services.messaging.message_interface import IMessageService
from app.services.onboarding.onboarding_service_interface import IOnboardingService
from app.services.localization.localization_interface import ILocalizationService


class OnboardingService(IOnboardingService):
    """Сервис для управления процессом онбординга пользователей"""

    # Константы для шагов онбординга
    STEP_WELCOME = "welcome"
    STEP_NAME = "name"
    STEP_AGE = "age"
    STEP_GENDER = "gender"
    STEP_HEIGHT = "height"
    STEP_CURRENT_WEIGHT = "current_weight"
    STEP_TARGET_WEIGHT = "target_weight"
    STEP_ACTIVITY_LEVEL = "activity_level"
    STEP_WEIGHT_GOAL = "weight_goal"
    STEP_DIET_PREFERENCE = "diet_preference"
    STEP_ALLERGIES = "allergies"
    STEP_DISLIKED_PRODUCTS = "disliked_products"
    # TODO Добавить шаг предпочтительные продукты
    STEP_BUDGET = "budget"
    # TODO Добавить шаг доп информация которую следует учесть для диеты
    STEP_COMPLETE = "complete"

    # Последовательность шагов онбординга
    ONBOARDING_STEPS = [
        STEP_WELCOME,
        STEP_NAME,
        STEP_AGE,
        STEP_GENDER,
        STEP_HEIGHT,
        STEP_CURRENT_WEIGHT,
        STEP_TARGET_WEIGHT,
        STEP_WEIGHT_GOAL,
        STEP_ACTIVITY_LEVEL,
        STEP_DIET_PREFERENCE,
        STEP_ALLERGIES,
        STEP_DISLIKED_PRODUCTS,
        STEP_BUDGET,
        STEP_COMPLETE
    ]

    def __init__(
            self,
            user_repository: IUserRepository,
            message_service: IMessageService,
            diet_service: IDietService,
            command_handler_service: ICommandHandler,
            localization_service: ILocalizationService
    ):
        """
        Инициализация сервиса онбординга

        Args:
            user_repository: Репозиторий для работы с пользователями
            message_service: Сервис для отправки сообщений
            diet_service: Сервис для генерации диет (опционально)
            command_handler_service: Сервис обработки команд
            localization_service: Сервис локализации
        """
        self.user_repository = user_repository
        self.message_service = message_service
        self.diet_service = diet_service
        self.command_handler_service = command_handler_service
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def start_registration(self, phone_number: str) -> Dict[str, Any]:
        """
        Начинает процесс регистрации нового пользователя

        Args:
            phone_number: Номер телефона пользователя

        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            # Создаем новую запись пользователя
            new_user = {
                "phone_number": phone_number,
                "name": "",
                "is_onboarding_completed": False,
                "onboarding_step": self.STEP_WELCOME,
                # TODO сохранять реально источник
                "registration_source": "whatsapp"
            }

            # Сохраняем в базу данных
            user_id = await self.user_repository.create(new_user)

            if not user_id:
                self.logger.error(f"Failed to create user with phone number {phone_number}")
                return {"success": False, "error": "Failed to create user"}

            return {
                "success": True,
                "action": "registration_started",
                "user_id": user_id
            }

        except Exception as e:
            self.logger.error(f"Error during registration start: {str(e)}")
            return {"success": False, "error": str(e)}

    async def continue_onboarding(self, user_id: str, message_text: str) -> Dict[str, Any]:
        """
        Продолжает процесс онбординга пользователя

        Args:
            user_id: ID Пользователя
            message_text: Текст сообщения

        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            if not user_id:
                self.logger.error(f"User ID missing")
                return {"success": False, "error": "User ID not found"}

            user = await self.user_repository.get_by_id(user_id)

            # Получаем язык пользователя
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            current_step = user.get("onboarding_step", self.STEP_WELCOME)
            phone_number = user.get('phone_number')
            self.logger.info(f"Processing onboarding step: '{current_step}'")

            # Определяем следующий шаг
            next_step = self.get_next_onboarding_step(current_step)

            # Обрабатываем текущий шаг и обновляем данные пользователя
            update_data = self._process_step(current_step, message_text)
            self.logger.info(f"Update data: '{update_data}'")

            if not update_data:
                # Если произошла ошибка, отправляем сообщение с просьбой повторить
                step_message = self._get_step_message(current_step, lang)
                await self.message_service.send_message(
                    phone_number,
                    self.localization_service.get_message(
                        LK.Onboarding.INVALID_INPUT,
                        lang,
                        step_message=step_message
                    ),
                    {
                        'onboarding_step': current_step,
                        'user_id': user_id
                    }
                )
                return {"success": False, "error": "Invalid input for onboarding step"}

            # Автоматически определяем цель по весу после ввода целевого веса
            if current_step == self.STEP_TARGET_WEIGHT and "target_weight" in update_data:
                target_weight = float(update_data["target_weight"])
                current_weight = float(user.get("current_weight", 0))

                # Определяем weight_goal на основе разницы весов
                weight_goal, weight_goal_message = self._determine_weight_goal(current_weight, target_weight, lang)
                update_data["weight_goal"] = weight_goal

                # Отправляем уведомление пользователю о цели
                if weight_goal_message:
                    await self.message_service.send_message(phone_number, weight_goal_message)

                # Пропускаем шаг запроса цели по весу
                if next_step == self.STEP_WEIGHT_GOAL:
                    next_step = self.get_next_onboarding_step(next_step)

            # Обновляем данные пользователя
            update_data["onboarding_step"] = next_step
            await self.user_repository.update(user_id, update_data)

            # Если онбординг завершен
            if next_step == self.STEP_COMPLETE:
                await self.complete_onboarding(user_id, phone_number)
                return {
                    "success": True,
                    "action": "onboarding_completed",
                    "user_id": user_id
                }

            # Отправляем сообщение для следующего шага
            next_step_message = self._get_step_message(next_step, lang)
            await self.message_service.send_message(phone_number, next_step_message, {
                'onboarding_step': next_step,
                'user_id': user_id
            })

            return {
                "success": True,
                "action": "onboarding_continued",
                "user_id": user_id,
                "current_step": current_step,
                "next_step": next_step
            }

        except Exception as e:
            self.logger.error(f"Error during onboarding continuation: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def complete_onboarding(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Завершает процесс онбординга и запускает генерацию диеты

        Args:
            user_id: ID пользователя
            phone_number: Номер телефона пользователя

        Returns:
            Dict[str, Any]: Результат завершения онбординга
        """
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)

        # Отмечаем онбординг как завершенный
        await self.user_repository.update(user_id, {"is_onboarding_completed": True})

        # Отправляем сообщение о завершении онбординга
        context = {
            "onboarding_step": "complete",
            "user_id": user_id
        }
        await self.message_service.send_message(
            phone_number,
            self.localization_service.get_message(LK.Onboarding.COMPLETED, lang),
            context
        )

        user = await self.user_repository.get_by_id(user_id)
        await self.command_handler_service.handle_command(user, "diet")

        return {
            "success": True,
            "action": "onboarding_completed",
            "user_id": user_id
        }

    def get_next_onboarding_step(self, current_step: str) -> str:
        """
        Возвращает следующий шаг онбординга

        Args:
            current_step: Текущий шаг

        Returns:
            str: Следующий шаг
        """
        try:
            current_index = self.ONBOARDING_STEPS.index(current_step)
            next_index = current_index + 1

            if next_index >= len(self.ONBOARDING_STEPS):
                return self.STEP_COMPLETE

            return self.ONBOARDING_STEPS[next_index]
        except ValueError:
            return self.STEP_NAME  # Если шаг не найден, начинаем с имени

    def _process_step(self, step: str, message_text: str) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает ответ пользователя на шаге онбординга

        Args:
            step: Текущий шаг
            message_text: Текст сообщения

        Returns:
            Optional[Dict[str, Any]]: Данные для обновления пользователя или None в случае ошибки
        """
        try:
            # Очищаем текст сообщения
            message_text = message_text.strip()

            # Обработка шага в зависимости от его типа
            processors = {
                self.STEP_WELCOME: self._process_welcome,
                self.STEP_NAME: self._process_name,
                self.STEP_AGE: self._process_age,
                self.STEP_GENDER: self._process_gender,
                self.STEP_HEIGHT: self._process_height,
                self.STEP_CURRENT_WEIGHT: self._process_current_weight,
                self.STEP_TARGET_WEIGHT: self._process_target_weight,
                self.STEP_ACTIVITY_LEVEL: self._process_activity_level,
                self.STEP_WEIGHT_GOAL: self._process_weight_goal,
                self.STEP_DIET_PREFERENCE: self._process_diet_preference,
                self.STEP_ALLERGIES: self._process_allergies,
                self.STEP_DISLIKED_PRODUCTS: self._process_disliked_products,
                self.STEP_BUDGET: self._process_budget
            }

            # Вызываем соответствующий обработчик для шага
            if step in processors:
                return processors[step](message_text)

            # Если шаг не распознан
            return {}

        except Exception as e:
            self.logger.error(f"Error processing onboarding step {step}: {str(e)}")
            return None

    # Методы обработки шагов онбординга...
    def _process_welcome(self) -> Optional[Dict[str, Any]]:
        """Обработка приветствия"""
        return {"onboarding_step": self.STEP_NAME}

    def _process_name(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка имени пользователя"""
        if len(message_text) < 2 or len(message_text) > 50:
            return None
        return {"name": message_text}

    def _process_age(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка возраста"""
        try:
            age = int(message_text)
            if age < 18 or age > 100:
                return None
            return {"age": age}
        except ValueError:
            return None

    def _process_gender(self, message_text: str, lang: str = None) -> Optional[Dict[str, Any]]:
        """Обработка пола"""
        gender_text = message_text.lower()

        # Локализованные ключевые слова для определения пола
        male_keywords = [
            self.localization_service.get_message(LK.Onboarding.Gender.MALE, lang),
            self.localization_service.get_message(LK.Onboarding.Gender.MALE_SHORT, lang),
            "1"  # Универсальный номер
        ]

        female_keywords = [
            self.localization_service.get_message(LK.Onboarding.Gender.FEMALE, lang),
            self.localization_service.get_message(LK.Onboarding.Gender.FEMALE_SHORT, lang),
            "2"  # Универсальный номер
        ]

        if any(keyword.lower() in gender_text for keyword in male_keywords if keyword):
            return {"gender": "male"}
        elif any(keyword.lower() in gender_text for keyword in female_keywords if keyword):
            return {"gender": "female"}
        else:
            return {"gender": "other"}

    def _process_height(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка роста"""
        try:
            height = float(message_text.replace(',', '.'))
            if height < 100 or height > 250:
                return None
            return {"height": height}
        except ValueError:
            return None

    def _process_current_weight(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка текущего веса"""
        try:
            weight = float(message_text.replace(',', '.'))
            if weight < 30 or weight > 300:
                return None
            return {"current_weight": weight}
        except ValueError:
            return None

    def _process_target_weight(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка целевого веса"""
        try:
            weight = float(message_text.replace(',', '.'))
            if weight < 30 or weight > 300:
                return None
            return {"target_weight": weight}
        except ValueError:
            return None

    def _process_activity_level(self, message_text: str, lang: str = None) -> Optional[Dict[str, Any]]:
        """Обработка уровня активности"""
        activity_text = message_text.lower()

        # Словарь для маппинга ключевых слов на уровни активности
        activity_keywords = {
            "sedentary": [
                self.localization_service.get_message(LK.Onboarding.ActivityLevel.SEDENTARY, lang),
                "1"
            ],
            "light": [
                self.localization_service.get_message(LK.Onboarding.ActivityLevel.LIGHT, lang),
                "2"
            ],
            "moderate": [
                self.localization_service.get_message(LK.Onboarding.ActivityLevel.MODERATE, lang),
                "3"
            ],
            "high": [
                self.localization_service.get_message(LK.Onboarding.ActivityLevel.HIGH, lang),
                "4"
            ],
            "very_high": [
                self.localization_service.get_message(LK.Onboarding.ActivityLevel.VERY_HIGH, lang),
                "5"
            ]
        }

        # Проверяем каждый уровень активности
        for level, keywords in activity_keywords.items():
            if any(keyword.lower() in activity_text for keyword in keywords if keyword):
                return {"activity_level": level}

        # По умолчанию умеренная активность
        return {"activity_level": "moderate"}

    def _process_weight_goal(self, message_text: str, lang: str = None) -> Optional[Dict[str, Any]]:
        """Обработка цели по весу"""
        goal_text = message_text.lower()

        # Словарь для маппинга ключевых слов на цели по весу
        weight_goal_keywords = {
            "lose": [
                self.localization_service.get_message(LK.Onboarding.WeightGoal.LOSE, lang),
                "1"
            ],
            "maintain": [
                self.localization_service.get_message(LK.Onboarding.WeightGoal.MAINTAIN, lang),
                "2"
            ],
            "gain": [
                self.localization_service.get_message(LK.Onboarding.WeightGoal.GAIN, lang),
                "3"
            ]
        }

        # Проверяем каждую цель по весу
        for goal, keywords in weight_goal_keywords.items():
            if any(keyword.lower() in goal_text for keyword in keywords if keyword):
                return {"weight_goal": goal}

        # По умолчанию цель - похудение
        return {"weight_goal": "lose"}

    def _process_diet_preference(self, message_text: str, lang: str = None) -> Optional[Dict[str, Any]]:
        """Обработка предпочтений в диете"""
        pref_text = message_text.lower()

        # Словарь для маппинга ключевых слов на предпочтения в диете
        diet_pref_keywords = {
            "regular": [
                self.localization_service.get_message(LK.Onboarding.DietPreference.REGULAR, lang),
                "1"
            ],
            "vegetarian": [
                self.localization_service.get_message(LK.Onboarding.DietPreference.VEGETARIAN, lang),
                "2"
            ],
            "vegan": [
                self.localization_service.get_message(LK.Onboarding.DietPreference.VEGAN, lang),
                "3"
            ],
            "low_carb": [
                self.localization_service.get_message(LK.Onboarding.DietPreference.LOW_CARB, lang),
                "4"
            ],
            "keto": [
                self.localization_service.get_message(LK.Onboarding.DietPreference.KETO, lang),
                "5"
            ],
            "gluten_free": [
                self.localization_service.get_message(LK.Onboarding.DietPreference.GLUTEN_FREE, lang),
                "6"
            ]
        }

        # Проверяем каждое предпочтение в диете
        for pref, keywords in diet_pref_keywords.items():
            if any(keyword.lower() in pref_text for keyword in keywords if keyword):
                return {"diet_preference": pref}

        # По умолчанию обычная диета
        return {"diet_preference": "regular"}

    def _process_allergies(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка аллергий"""
        # Получаем список ключевых слов для отрицательного ответа из локализации
        if self._is_negative_answer(message_text):
            return {"allergies": []}

        allergies = [a.strip() for a in message_text.split(',')]
        return {"allergies": allergies}

    def _process_disliked_products(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка нелюбимых продуктов"""
        if self._is_negative_answer(message_text):
            return {"disliked_products": []}

        disliked = [p.strip() for p in message_text.split(',')]
        return {"disliked_products": disliked}

    def _process_budget(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка бюджета"""
        try:
            # Проверяем на ключевые слова неограниченного бюджета
            message_lower = message_text.lower()

            # Используем локализацию для получения ключевых слов
            if self._is_unlimited_budget(message_lower):
                self.logger.info(f"Detected unlimited budget: '{message_text}'")
                return {"budget_limit": 10000, "budget_unlimited": True}

            # Если нет ключевых слов, пробуем преобразовать в число
            budget = float(message_text.replace(',', '.'))
            if budget < 0:
                return None
            return {"budget_limit": budget, "budget_unlimited": False}
        except ValueError:
            self.logger.warning(f"Could not parse budget: '{message_text}'")
            return None

    def _determine_weight_goal(self, current_weight: float, target_weight: float, lang: str = 'en') -> Tuple[str, str]:
        """
        Определяет цель по весу на основе текущего и целевого весов

        Args:
            current_weight: Текущий вес
            target_weight: Целевой вес
            lang: Код языка

        Returns:
            Tuple[str, str]: (weight_goal, сообщение пользователю)
        """
        if target_weight < current_weight - 0.5:
            return "lose", self.localization_service.get_message(LK.Onboarding.WEIGHT_GOAL_DETERMINED_LOSE, lang)
        elif target_weight > current_weight + 0.5:
            return "gain", self.localization_service.get_message(LK.Onboarding.WEIGHT_GOAL_DETERMINED_GAIN, lang)
        else:
            return "maintain", self.localization_service.get_message(LK.Onboarding.WEIGHT_GOAL_DETERMINED_MAINTAIN,
                                                                     lang)

    def _get_step_message(self, step: str, lang: str = 'en') -> str:
        """
        Получает локализованное сообщение для шага онбординга

        Args:
            step: Шаг онбординга
            lang: Код языка

        Returns:
            str: Локализованное сообщение для шага
        """
        # Маппинг шагов и ключей локализации
        step_keys = {
            self.STEP_WELCOME: LK.Onboarding.WELCOME,
            self.STEP_NAME: LK.Onboarding.NAME_REQUEST,
            self.STEP_AGE: LK.Onboarding.AGE_REQUEST,
            self.STEP_GENDER: LK.Onboarding.GENDER_REQUEST,
            self.STEP_HEIGHT: LK.Onboarding.HEIGHT_REQUEST,
            self.STEP_CURRENT_WEIGHT: LK.Onboarding.CURRENT_WEIGHT_REQUEST,
            self.STEP_TARGET_WEIGHT: LK.Onboarding.TARGET_WEIGHT_REQUEST,
            self.STEP_WEIGHT_GOAL: LK.Onboarding.WEIGHT_GOAL_REQUEST,
            self.STEP_ACTIVITY_LEVEL: LK.Onboarding.ACTIVITY_LEVEL_REQUEST,
            self.STEP_DIET_PREFERENCE: LK.Onboarding.DIET_PREFERENCE_REQUEST,
            self.STEP_ALLERGIES: LK.Onboarding.ALLERGIES_REQUEST,
            self.STEP_DISLIKED_PRODUCTS: LK.Onboarding.DISLIKED_PRODUCTS_REQUEST,
            self.STEP_BUDGET: LK.Onboarding.BUDGET_REQUEST,
            self.STEP_COMPLETE: LK.Onboarding.COMPLETED
        }

        # Получаем ключ для шага
        key = step_keys.get(step)
        if not key:
            return f"Step {step}"

        # Получаем сообщение для шага
        message = self.localization_service.get_message(key, lang)

        # Получаем пример для шага, если есть
        example_key = f"{key}Example"
        try:
            example = self.localization_service.get_message(example_key, lang)
            if example:
                message += f"\n\n{example}"
        except:
            # Если примера нет, игнорируем
            pass

        return message

    def _is_negative_answer(self, text: str, lang: str = None) -> bool:
        """Проверяет, является ли текст отрицательным ответом"""
        text_lower = text.lower()
        negative_answers = [
            self.localization_service.get_message(LK.Onboarding.Answers.NO, lang),
            self.localization_service.get_message(LK.Onboarding.Answers.NONE, lang),
            self.localization_service.get_message(LK.Onboarding.Answers.NO_HAVE, lang),
            "no"  # Универсальное слово для совместимости
        ]
        return any(ans.lower() in text_lower for ans in negative_answers if ans)

    def _is_unlimited_budget(self, text: str, lang: str = None) -> bool:
        """Проверяет, указывает ли текст на неограниченный бюджет"""
        unlimited_keywords = [
            self.localization_service.get_message(LK.Onboarding.Budget.UNLIMITED, lang),
            self.localization_service.get_message(LK.Onboarding.Budget.NO_LIMIT, lang),
            self.localization_service.get_message(LK.Onboarding.Budget.ANY, lang),
            "unlimited"  # Универсальное слово для совместимости
        ]
        return any(keyword.lower() in text for keyword in unlimited_keywords if keyword)
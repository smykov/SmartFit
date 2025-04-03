import logging
from typing import Dict, Any, List, Optional, Tuple

from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.messaging.message_interface import IMessageService
from app.localization.onboarding_messages import OnboardingMessages
from config import settings


class OnboardingService:
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
    STEP_BUDGET = "budget"
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
        STEP_ACTIVITY_LEVEL,
        STEP_WEIGHT_GOAL,
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
        diet_generator_service=None
    ):
        """
        Инициализация сервиса онбординга
        
        Args:
            user_repository: Репозиторий для работы с пользователями
            message_service: Сервис для отправки сообщений
            diet_generator_service: Сервис для генерации диет (опционально)
        """
        self.user_repository = user_repository
        self.message_service = message_service
        self.diet_generator_service = diet_generator_service
        self.messages = OnboardingMessages()
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
                "registration_source": "whatsapp"
            }
            
            # Сохраняем в базу данных
            user_id = await self.user_repository.create(new_user)
            
            if not user_id:
                self.logger.error(f"Не удалось создать пользователя с номером {phone_number}")
                return {"success": False, "error": "Failed to create user"}
            
            # Обновляем шаг онбординга
            await self.user_repository.update(user_id, {"onboarding_step": self.STEP_NAME})

            # Отправляем приветственное сообщение
            await self.message_service.send_template_message(phone_number, "welcome")

            return {
                "success": True,
                "action": "registration_started",
                "user_id": user_id
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при начале регистрации: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def continue_onboarding(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Продолжает процесс онбординга пользователя
        
        Args:
            user: Данные пользователя
            message_text: Текст сообщения
        
        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            user_id = user.get("id")
            
            if not user_id:
                self.logger.error(f"Отсутствует ID пользователя: {user.get('phone_number')}")
                return {"success": False, "error": "User ID not found"}
            
            current_step = user.get("onboarding_step", self.STEP_WELCOME)
            phone_number = user.get('phone_number')
            
            # Определяем следующий шаг
            next_step = self._get_next_step(current_step)
            
            # Обрабатываем текущий шаг и обновляем данные пользователя
            update_data = self._process_step(current_step, message_text)
            
            if not update_data:
                # Если произошла ошибка, отправляем сообщение с просьбой повторить
                step_message = self._get_step_message(current_step)
                await self.message_service.send_message(
                    phone_number,
                    self.messages.INVALID_INPUT_RETRY.format(step_message=step_message),
                    current_step
                )
                return {"success": False, "error": "Invalid input for onboarding step"}
            
            # Автоматически определяем цель по весу после ввода целевого веса
            if current_step == self.STEP_TARGET_WEIGHT and "target_weight" in update_data:
                target_weight = float(update_data["target_weight"])
                current_weight = float(user.get("current_weight", 0))
                
                # Определяем weight_goal на основе разницы весов
                weight_goal, weight_goal_message = self._determine_weight_goal(current_weight, target_weight)
                update_data["weight_goal"] = weight_goal
                
                # Отправляем уведомление пользователю о цели
                if weight_goal_message:
                    await self.message_service.send_message(phone_number, weight_goal_message)
                
                # Пропускаем шаг запроса цели по весу
                if next_step == self.STEP_WEIGHT_GOAL:
                    next_step = self._get_next_step(next_step)
            
            # Обновляем данные пользователя
            update_data["onboarding_step"] = next_step
            await self.user_repository.update(user_id, update_data)
            
            # Если онбординг завершен
            if next_step == self.STEP_COMPLETE:
                await self._complete_onboarding(user_id, phone_number)
                return {
                    "success": True,
                    "action": "onboarding_completed",
                    "user_id": user_id
                }
            
            # Отправляем сообщение для следующего шага
            next_step_message = self._get_step_message(next_step)
            await self.message_service.send_message(phone_number, next_step_message, next_step)
            
            return {
                "success": True,
                "action": "onboarding_continued",
                "user_id": user_id,
                "current_step": current_step,
                "next_step": next_step
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при продолжении онбординга: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _complete_onboarding(self, user_id: str, phone_number: str) -> None:
        """
        Завершает процесс онбординга и запускает генерацию диеты
        
        Args:
            user_id: ID пользователя
            phone_number: Номер телефона пользователя
        """
        # Отмечаем онбординг как завершенный
        await self.user_repository.update(user_id, {"is_onboarding_completed": True})
        
        # Отправляем сообщение о завершении онбординга
        await self.message_service.send_message(
            phone_number, 
            self.messages.ONBOARDING_COMPLETED
        )
        
        await self.message_service.send_message(
            phone_number,
            self.messages.DIET_GENERATION_STARTED
        )
        
        # Если есть сервис генерации диет, запускаем генерацию
        if self.diet_generator_service:
            await self.diet_generator_service.start_short_diet_generation(phone_number, user_id)
    
    def _get_next_step(self, current_step: str) -> str:
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
            self.logger.error(f"Ошибка при обработке шага онбординга {step}: {str(e)}")
            return None
    
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
    
    def _process_gender(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка пола"""
        gender_text = message_text.lower()
        if "муж" in gender_text:
            return {"gender": "male"}
        elif "жен" in gender_text:
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
    
    def _process_activity_level(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка уровня активности"""
        activity_text = message_text.lower()
        # TODO ДОбавить в локализация ответы
        if "сид" in activity_text or "низк" in activity_text or "1" in activity_text:
            return {"activity_level": "sedentary"}
        elif "легк" in activity_text or "2" in activity_text:
            return {"activity_level": "light"}
        elif "сред" in activity_text or "умер" in activity_text or "3" in activity_text:
            return {"activity_level": "moderate"}
        elif "высок" in activity_text or "4" in activity_text:
            return {"activity_level": "high"}
        elif "очень высок" in activity_text or "спорт" in activity_text or "5" in activity_text:
            return {"activity_level": "very_high"}
        else:
            return {"activity_level": "moderate"}  # По умолчанию
    
    def _process_weight_goal(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка цели по весу"""
        goal_text = message_text.lower()
        # TODO ДОбавить в локализация ответы
        if "похуд" in goal_text or "сниж" in goal_text or "1" in goal_text:
            return {"weight_goal": "lose"}
        elif "поддерж" in goal_text or "сохран" in goal_text or "2" in goal_text:
            return {"weight_goal": "maintain"}
        elif "набр" in goal_text or "увел" in goal_text or "3" in goal_text:
            return {"weight_goal": "gain"}
        else:
            return {"weight_goal": "lose"}  # По умолчанию для сервиса похудения
    
    def _process_diet_preference(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка предпочтений в диете"""
        pref_text = message_text.lower()
        # TODO ДОбавить в локализация ответы
        if "обыч" in pref_text or "1" in pref_text:
            return {"diet_preference": "regular"}
        elif "вегетар" in pref_text or "2" in pref_text:
            return {"diet_preference": "vegetarian"}
        elif "веган" in pref_text or "3" in pref_text:
            return {"diet_preference": "vegan"}
        elif "низкоуглевод" in pref_text or "4" in pref_text:
            return {"diet_preference": "low_carb"}
        elif "кето" in pref_text or "5" in pref_text:
            return {"diet_preference": "keto"}
        elif "безглютен" in pref_text or "6" in pref_text:
            return {"diet_preference": "gluten_free"}
        else:
            return {"diet_preference": "regular"}  # По умолчанию
    
    def _process_allergies(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка аллергий"""
        # TODO ДОбавить в локализация ответы
        if message_text.lower() in ["нет", "не имею", "отсутствуют", "no"]:
            return {"allergies": []}
            
        allergies = [a.strip() for a in message_text.split(',')]
        return {"allergies": allergies}
    
    def _process_disliked_products(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка нелюбимых продуктов"""
        # TODO ДОбавить в локализация ответы
        if message_text.lower() in ["нет", "не имею", "отсутствуют", "no"]:
            return {"disliked_products": []}
            
        disliked = [p.strip() for p in message_text.split(',')]
        return {"disliked_products": disliked}
    
    def _process_budget(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Обработка бюджета"""
        try:
            # TODO ДОбавить в локализация ответы
            # Проверяем на ключевые слова неограниченного бюджета
            message_lower = message_text.lower()
            unlimited_keywords = [
                "нет", "неограничен", "без ограничений", "без учета", "не важно",
                "любой", "не имеет значения", "без бюджета", "неограниченный",
                "no limit", "unlimited"
            ]
            
            # Проверка на ключевые слова
            if any(keyword in message_lower for keyword in unlimited_keywords):
                self.logger.info(f"Распознан неограниченный бюджет: '{message_text}'")
                return {"budget_limit": 10000, "budget_unlimited": True}
                
            # Если нет ключевых слов, пробуем преобразовать в число
            budget = float(message_text.replace(',', '.'))
            if budget < 0:
                return None
            return {"budget_limit": budget, "budget_unlimited": False}
        except ValueError:
            self.logger.warning(f"Не удалось распознать бюджет: '{message_text}'")
            return None
    
    def _determine_weight_goal(self, current_weight: float, target_weight: float) -> Tuple[str, str]:
        """
        Определяет цель по весу на основе текущего и целевого весов
        
        Args:
            current_weight: Текущий вес
            target_weight: Целевой вес
            
        Returns:
            Tuple[str, str]: (weight_goal, сообщение пользователю)
        """
        if target_weight < current_weight - 0.5:
            return "lose", self.messages.WEIGHT_GOAL_DETERMINED_LOSE
        elif target_weight > current_weight + 0.5:
            return "gain", self.messages.WEIGHT_GOAL_DETERMINED_GAIN
        else:
            return "maintain", self.messages.WEIGHT_GOAL_DETERMINED_MAINTAIN
    
    def _get_step_message(self, step: str) -> str:
        """
        Возвращает сообщение для шага онбординга с примерами
        
        Args:
            step: Шаг онбординга
            
        Returns:
            str: Сообщение с инструкциями и примерами
        """
        # Получаем сообщение для шага из локализации
        message = self.messages.get_step_message(step)
        
        # Добавляем пример к сообщению
        if step in self.messages.EXAMPLES:
            message += f"\n{self.messages.EXAMPLES[step]}"
            
        return message
    

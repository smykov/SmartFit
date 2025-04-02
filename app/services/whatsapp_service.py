import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
import json
from twilio.rest import Client
from enum import Enum
import re

from config import settings
from app.db.firebase import firebase_client
from app.services.openai_service import openai_service

logger = logging.getLogger(__name__)

# Инициализация Twilio клиента для WhatsApp API
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    TEMPLATE = "template"

class WhatsAppService:
    """Сервис для работы с WhatsApp API"""
    
    def __init__(self):
        self.from_phone_number = settings.TWILIO_PHONE_NUMBER
        self.ONBOARDING_STEPS = [
            "welcome",
            "name",
            "age",
            "gender",
            "height",
            "current_weight",
            "target_weight",
            "activity_level",
            "weight_goal",
            "diet_preference",
            "allergies",
            "disliked_products",
            "budget",
            "complete"
        ]
    
    async def process_incoming_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает входящее сообщение из WhatsApp
        
        Args:
            body: Данные входящего сообщения
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            logger.info(f"Получено новое сообщение WhatsApp: {json.dumps(body, ensure_ascii=False)}")
            
            # Извлекаем данные сообщения
            phone_number, message_text, message_type = self._extract_message_data(body)
            
            if not phone_number or not message_text:
                logger.error("Не удалось извлечь номер телефона или текст сообщения")
                return {"success": False, "error": "Invalid message format"}
            
            # Проверяем, существует ли пользователь
            user = firebase_client.query_documents("users", "phone_number", "==", phone_number)
            
            if not user:
                # Если пользователь не существует, начинаем процесс регистрации
                logger.info(f"Новый пользователь с номером {phone_number}. Начинаем регистрацию.")
                return await self._start_registration(phone_number)
            
            # Пользователь существует
            user = user[0]
            
            # Проверяем, завершил ли пользователь онбординг
            if not user.get("is_onboarding_completed", False):
                logger.info(f"Пользователь {phone_number} продолжает онбординг")
                return await self._continue_onboarding(user, message_text)
            
            # Если онбординг завершен, обрабатываем обычное сообщение
            logger.info(f"Обработка обычного сообщения от пользователя {phone_number}")
            return await self._process_regular_message(user, message_text, message_type)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке входящего сообщения: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_message(self, to_phone: str, message: str) -> bool:
        """
        Отправляет текстовое сообщение по WhatsApp
        
        Args:
            to_phone: Номер телефона получателя
            message: Текст сообщения
            
        Returns:
            bool: Результат отправки
        """
        try:
            # Нормализуем номер телефона (добавляем +, если его нет)
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"
            
            # Отправляем сообщение через Twilio
            message = twilio_client.messages.create(
                from_=f"whatsapp:{self.from_phone_number}",
                body=message,
                to=f"whatsapp:{to_phone}"
            )
            
            logger.info(f"Сообщение успешно отправлено: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            return False
    
    async def send_template_message(self, to_phone: str, template_name: str, params: List[str] = None) -> bool:
        """
        Отправляет шаблонное сообщение через WhatsApp Business API
        
        Args:
            to_phone: Номер телефона получателя
            template_name: Название шаблона
            params: Параметры для шаблона
            
        Returns:
            bool: Результат отправки
        """
        try:
            # Нормализуем номер телефона
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"
            
            # Для MVP упрощенно используем обычное сообщение вместо шаблона
            # В реальном проекте здесь надо использовать WhatsApp Business API для шаблонов
            
            # Базовые шаблоны для MVP
            templates = {
                "welcome": "👋 Привет! Добро пожаловать в GuateFit - твой персональный ассистент для похудения. Я помогу тебе создать план питания, который подходит именно тебе, учитывая местные продукты и твой бюджет. Давай начнем настройку! Как тебя зовут?",
                
                "diet_created": "🎉 Твой план питания готов! Я подобрал блюда, учитывая твои параметры и предпочтения. Посмотри план и дай мне знать, если хочешь что-то изменить.",
                
                "weight_reminder": "⚖️ Привет! Не забудь записать свой вес сегодня. Это поможет отслеживать прогресс. Просто напиши 'вес XX', где XX - твой вес в килограммах.",
                
                "water_reminder": "💧 Не забывай пить воду! Отправь 'вода X', где X - количество стаканов, которые ты выпил(а).",
                
                "weekly_report": "📊 Вот твой еженедельный отчет:\n{progress}\n\nОтличная работа! Продолжай в том же духе! 💪"
            }
            
            message_text = templates.get(template_name, "Сообщение шаблона")
            
            # Заменяем параметры, если они есть
            if params:
                for i, param in enumerate(params):
                    message_text = message_text.replace(f"{{{i}}}", param)
            
            # Отправляем сообщение
            return await self.send_message(to_phone, message_text)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке шаблонного сообщения: {str(e)}")
            return False
    
    def _extract_message_data(self, body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Извлекает данные из входящего сообщения WhatsApp
        
        Args:
            body: Данные сообщения
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: (номер телефона, текст сообщения, тип сообщения)
        """
        try:
            # Пример обработки сообщения от Twilio
            # Примечание: формат может отличаться в зависимости от провайдера WhatsApp API
            
            phone_number = body.get("From", "").replace("whatsapp:", "")
            message_text = body.get("Body", "")
            message_type = MessageType.TEXT  # По умолчанию текстовое сообщение
            
            # Проверяем, есть ли медиа в сообщении
            if "MediaUrl0" in body:
                message_type = MessageType.MEDIA
                # Для MVP не обрабатываем медиафайлы, но могли бы сохранить URL
            
            return phone_number, message_text, message_type
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных сообщения: {str(e)}")
            return None, None, None
    
    async def _start_registration(self, phone_number: str) -> Dict[str, Any]:
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
                "onboarding_step": "welcome",
                "registration_source": "whatsapp"
            }
            
            # Сохраняем в базу данных
            user_id = firebase_client.add_document("users", new_user)
            
            if not user_id:
                logger.error(f"Не удалось создать пользователя с номером {phone_number}")
                return {"success": False, "error": "Failed to create user"}
            
            # Отправляем приветственное сообщение
            await self.send_template_message(phone_number, "welcome")
            
            # Обновляем шаг онбординга
            firebase_client.update_document("users", user_id, {"onboarding_step": "name"})
            
            return {
                "success": True,
                "action": "registration_started",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка при начале регистрации: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _continue_onboarding(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
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
            current_step = user.get("onboarding_step", "welcome")
            
            # Определяем следующий шаг
            next_step = self._get_next_onboarding_step(current_step)
            
            # Обрабатываем текущий шаг и обновляем данные пользователя
            update_data = self._process_onboarding_step(current_step, message_text)
            
            if not update_data:
                # Если произошла ошибка, отправляем сообщение с просьбой повторить
                await self.send_message(
                    user["phone_number"],
                    "Извините, я не смог обработать ваш ответ. Пожалуйста, попробуйте еще раз."
                )
                return {"success": False, "error": "Invalid input for onboarding step"}
            
            # Обновляем данные пользователя
            update_data["onboarding_step"] = next_step
            firebase_client.update_document("users", user_id, update_data)
            
            # Если онбординг завершен
            if next_step == "complete":
                firebase_client.update_document("users", user_id, {"is_onboarding_completed": True})
                await self.send_message(
                    user["phone_number"],
                    "🎉 Отлично! Настройка завершена. Теперь я создам для тебя персональный план питания на основе твоих данных."
                )
                
                # В реальном проекте здесь бы запускалась асинхронная задача на генерацию диеты
                # Для MVP просто уведомляем пользователя
                await self.send_message(
                    user["phone_number"],
                    "Я подготовлю для тебя план и скоро пришлю его. Это займет несколько минут."
                )
                
                return {
                    "success": True,
                    "action": "onboarding_completed",
                    "user_id": user_id
                }
            
            # Отправляем сообщение для следующего шага
            next_step_message = self._get_onboarding_step_message(next_step)
            await self.send_message(user["phone_number"], next_step_message)
            
            return {
                "success": True,
                "action": "onboarding_continued",
                "user_id": user_id,
                "current_step": current_step,
                "next_step": next_step
            }
            
        except Exception as e:
            logger.error(f"Ошибка при продолжении онбординга: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _process_regular_message(self, user: Dict[str, Any], message_text: str, message_type: str) -> Dict[str, Any]:
        """
        Обрабатывает обычное сообщение от пользователя
        
        Args:
            user: Данные пользователя
            message_text: Текст сообщения
            message_type: Тип сообщения
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            user_id = user.get("id")
            phone_number = user.get("phone_number")
            
            # Обновляем время последнего взаимодействия
            firebase_client.update_document("users", user_id, {"last_interaction": "now"})
            
            # Проверяем специальные команды
            
            # Команда для записи веса
            weight_match = re.match(r'^вес\s+(\d+[.,]?\d*)$', message_text.lower())
            if weight_match:
                weight = float(weight_match.group(1).replace(',', '.'))
                await self._record_weight(user_id, weight)
                await self.send_message(
                    phone_number,
                    f"✅ Отлично! Я записал твой вес: {weight} кг. Продолжай отслеживать прогресс регулярно."
                )
                return {"success": True, "action": "weight_recorded"}
            
            # Команда для записи потребления воды
            water_match = re.match(r'^вода\s+(\d+[.,]?\d*)$', message_text.lower())
            if water_match:
                amount = float(water_match.group(1).replace(',', '.'))
                await self._record_water_intake(user_id, amount)
                await self.send_message(
                    phone_number,
                    f"💧 Отлично! Я записал потребление воды: {amount} стаканов. Продолжай в том же духе!"
                )
                return {"success": True, "action": "water_recorded"}
            
            # Команда для генерации диеты
            if "диета" in message_text.lower() or "план" in message_text.lower():
                await self.send_message(
                    phone_number,
                    "🥗 Я начинаю создавать для тебя новый план питания. Это займет несколько минут."
                )
                # В реальном проекте здесь бы запускалась асинхронная задача на генерацию диеты
                return {"success": True, "action": "diet_generation_started"}
            
            # Команда для получения статистики
            if "статистика" in message_text.lower() or "прогресс" in message_text.lower():
                await self.send_message(
                    phone_number,
                    "📊 Я подготавливаю статистику твоего прогресса. Подожди немного."
                )
                # В реальном проекте здесь бы формировалась статистика
                return {"success": True, "action": "stats_requested"}
            
            # Обработка обычного запроса с помощью OpenAI
            response = await openai_service.answer_nutrition_question(user_id, message_text)
            await self.send_message(phone_number, response)
            
            return {"success": True, "action": "ai_response_sent"}
            
        except Exception as e:
            logger.error(f"Ошибка при обработке обычного сообщения: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_next_onboarding_step(self, current_step: str) -> str:
        """Возвращает следующий шаг онбординга"""
        try:
            current_index = self.ONBOARDING_STEPS.index(current_step)
            next_index = current_index + 1
            
            if next_index >= len(self.ONBOARDING_STEPS):
                return "complete"
            
            return self.ONBOARDING_STEPS[next_index]
        except ValueError:
            return "name"  # Если шаг не найден, начинаем с имени
    
    def _process_onboarding_step(self, step: str, message_text: str) -> Optional[Dict[str, Any]]:
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
            
            if step == "name":
                # Валидация имени
                if len(message_text) < 2 or len(message_text) > 50:
                    return None
                return {"name": message_text}
                
            elif step == "age":
                # Валидация возраста
                try:
                    age = int(message_text)
                    if age < 18 or age > 100:
                        return None
                    return {"age": age}
                except ValueError:
                    return None
                
            elif step == "gender":
                # Валидация пола
                gender_text = message_text.lower()
                if "муж" in gender_text:
                    return {"gender": "male"}
                elif "жен" in gender_text:
                    return {"gender": "female"}
                else:
                    return {"gender": "other"}
                
            elif step == "height":
                # Валидация роста
                try:
                    height = float(message_text.replace(',', '.'))
                    if height < 100 or height > 250:
                        return None
                    return {"height": height}
                except ValueError:
                    return None
                
            elif step == "current_weight":
                # Валидация текущего веса
                try:
                    weight = float(message_text.replace(',', '.'))
                    if weight < 30 or weight > 300:
                        return None
                    return {"current_weight": weight}
                except ValueError:
                    return None
                
            elif step == "target_weight":
                # Валидация целевого веса
                try:
                    weight = float(message_text.replace(',', '.'))
                    if weight < 30 or weight > 300:
                        return None
                    return {"target_weight": weight}
                except ValueError:
                    return None
                
            elif step == "activity_level":
                # Валидация уровня активности
                activity_text = message_text.lower()
                
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
                
            elif step == "weight_goal":
                # Валидация цели по весу
                goal_text = message_text.lower()
                
                if "похуд" in goal_text or "сниж" in goal_text or "1" in goal_text:
                    return {"weight_goal": "lose"}
                elif "поддерж" in goal_text or "сохран" in goal_text or "2" in goal_text:
                    return {"weight_goal": "maintain"}
                elif "набр" in goal_text or "увел" in goal_text or "3" in goal_text:
                    return {"weight_goal": "gain"}
                else:
                    return {"weight_goal": "lose"}  # По умолчанию для сервиса похудения
                
            elif step == "diet_preference":
                # Валидация предпочтений в диете
                pref_text = message_text.lower()
                
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
                
            elif step == "allergies":
                # Обработка аллергий
                if message_text.lower() in ["нет", "не имею", "отсутствуют", "no"]:
                    return {"allergies": []}
                
                allergies = [a.strip() for a in message_text.split(',')]
                return {"allergies": allergies}
                
            elif step == "disliked_products":
                # Обработка нелюбимых продуктов
                if message_text.lower() in ["нет", "не имею", "отсутствуют", "no"]:
                    return {"disliked_products": []}
                
                disliked = [p.strip() for p in message_text.split(',')]
                return {"disliked_products": disliked}
                
            elif step == "budget":
                # Валидация бюджета
                try:
                    budget = float(message_text.replace(',', '.'))
                    if budget < 0:
                        return None
                    return {"budget_limit": budget}
                except ValueError:
                    return None
            
            # Если шаг не распознан
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка при обработке шага онбординга {step}: {str(e)}")
            return None
    
    def _get_onboarding_step_message(self, step: str) -> str:
        """Возвращает сообщение для шага онбординга"""
        messages = {
            "name": "Как тебя зовут?",
            
            "age": "Сколько тебе лет?",
            
            "gender": "Укажи свой пол (мужской/женский/другой):",
            
            "height": "Какой у тебя рост в сантиметрах?",
            
            "current_weight": "Какой у тебя текущий вес в килограммах?",
            
            "target_weight": "Какой вес ты хочешь достичь (в килограммах)?",
            
            "activity_level": """Оцени свой уровень физической активности:
1. Сидячий образ жизни (мало или совсем нет физических нагрузок)
2. Легкая активность (легкие упражнения 1-3 раза в неделю)
3. Умеренная активность (умеренные упражнения 3-5 раз в неделю)
4. Высокая активность (интенсивные тренировки 6-7 раз в неделю)
5. Очень высокая активность (физическая работа или 2 тренировки в день)

Ответь номером или напиши своими словами:""",
            
            "weight_goal": """Какая у тебя цель по весу?
1. Похудеть
2. Поддерживать текущий вес
3. Набрать вес

Ответь номером или напиши своими словами:""",
            
            "diet_preference": """Какие у тебя предпочтения в питании?
1. Обычная диета (без ограничений)
2. Вегетарианская (без мяса, но с яйцами и молочными продуктами)
3. Веганская (только растительная пища)
4. Низкоуглеводная (ограничение углеводов)
5. Кето (высокое содержание жиров, очень низкое содержание углеводов)
6. Безглютеновая (без пшеницы, ржи и ячменя)

Ответь номером или напиши своими словами:""",
            
            "allergies": "Есть ли у тебя пищевые аллергии? Перечисли через запятую или напиши 'нет':",
            
            "disliked_products": "Есть ли продукты, которые ты не любишь или не хочешь включать в диету? Перечисли через запятую или напиши 'нет':",
            
            "budget": "Какой у тебя недельный бюджет на продукты питания (в кетцалях)?"
        }
        
        return messages.get(step, "Пожалуйста, ответь на вопрос:")
    
    async def _record_weight(self, user_id: str, weight: float) -> bool:
        """
        Записывает вес пользователя
        
        Args:
            user_id: ID пользователя
            weight: Вес в кг
            
        Returns:
            bool: Результат операции
        """
        try:
            # Получаем текущую дату
            from datetime import datetime, date
            import pytz
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()
            
            # Получаем текущие данные пользователя
            user_data = firebase_client.get_document("users", user_id)
            
            if not user_data:
                return False
            
            # Обновляем текущий вес
            firebase_client.update_document("users", user_id, {"current_weight": weight})
            
            # Добавляем запись в историю веса
            weight_history = user_data.get("weight_history", {})
            weight_history[today] = weight
            
            firebase_client.update_document("users", user_id, {"weight_history": weight_history})
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при записи веса: {str(e)}")
            return False
    
    async def _record_water_intake(self, user_id: str, amount: float) -> bool:
        """
        Записывает потребление воды
        
        Args:
            user_id: ID пользователя
            amount: Количество стаканов воды
            
        Returns:
            bool: Результат операции
        """
        try:
            # Получаем текущую дату
            from datetime import datetime, date
            import pytz
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()
            
            # Получаем текущие данные пользователя
            user_data = firebase_client.get_document("users", user_id)
            
            if not user_data:
                return False
            
            # Преобразуем стаканы в миллилитры (примерно 250 мл в стакане)
            amount_ml = amount * 250
            
            # Добавляем запись в историю потребления воды
            water_history = user_data.get("water_intake_history", {})
            
            # Если на сегодня уже есть запись, добавляем к ней
            if today in water_history:
                water_history[today] += amount_ml
            else:
                water_history[today] = amount_ml
            
            firebase_client.update_document("users", user_id, {"water_intake_history": water_history})
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при записи потребления воды: {str(e)}")
            return False

# Создаем экземпляр сервиса WhatsApp
whatsapp_service = WhatsAppService()

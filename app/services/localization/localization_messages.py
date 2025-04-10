# app/services/localization/localization_messages.py

"""
Централизованное хранилище локализованных сообщений
"""
from calendar import weekheader

LOCALIZED_MESSAGES = {
    "es": {  # Испанский (исходный)
        "greeting": "👋 ¡Hola! Bienvenido a GuateFit - tu asistente personal para perder peso.",
        "onboarding": {
            "welcome": "Te ayudaré a crear un plan de alimentación adaptado a ti, teniendo en cuenta los productos locales y tu presupuesto. ¡Comencemos con la configuración!",
            "name": "¿Cómo te llamas?",
            "age": "¿Cuántos años tienes?",
            "gender": "¿Cuál es tu sexo? (masculino/femenino/otro):",
            "height": "¿Cuál es tu altura en centímetros?",
            "current_weight": "¿Cuánto pesas actualmente en kilogramos?",
            "target_weight": "¿Qué peso quieres alcanzar (en kilogramos)?",
            "activity_level": """Evalúa tu nivel de actividad física:
1. Estilo de vida sedentario (poca o ninguna actividad física)
2. Actividad ligera (ejercicios ligeros 1-3 veces por semana)
3. Actividad moderada (ejercicios moderados 3-5 veces por semana)
4. Actividad alta (entrenamientos intensivos 6-7 veces por semana)
5. Actividad muy alta (trabajo físico o 2 entrenamientos al día)

Responde con un número o dímelo con tus propias palabras:""",
            "weight_goal": """¿Cuál es tu objetivo de peso?
1. Perder peso
2. Mantener tu peso actual
3. Ganar peso

Responde con un número o dímelo con tus propias palabras:""",
            "diet_preference": """¿Qué preferencias alimentarias tienes?
1. Dieta regular (sin restricciones)
2. Vegetariana (sin carne, pero con huevos y lácteos)
3. Vegana (solo alimentos vegetales)
4. Baja en carbohidratos (restricción de carbohidratos)
5. Keto (alto contenido de grasas, muy bajo en carbohidratos)
6. Sin gluten (sin trigo, centeno ni cebada)

Responde con un número o dímelo con tus propias palabras:""",
            "allergies": "¿Tienes alergias alimentarias? Enuméralas separadas por comas o escribe 'no':",
            "disliked_products": "¿Hay productos que no te gustan o no quieres incluir en tu dieta? Enuméralos separados por comas o escribe 'no':",
            "budget": "¿Cuál es tu presupuesto semanal para alimentos (en quetzales)?",
            "completed": "🎉 ¡Felicidades! Has completado la configuración. Ahora puedes usar comandos como 'plan', 'estadísticas', 'peso XX', 'agua X' para interactuar con GuateFit."
        },
        "diet": {
            "created": "🎉 ¡Tu plan de alimentación está listo! He seleccionado platos teniendo en cuenta tus parámetros y preferencias. Revisa el plan y hazme saber si quieres cambiar algo.\n\n📊 Para ver tus estadísticas y progreso, escribe 'estadísticas' o 'progreso' en cualquier momento.",
            "updating": "Estoy ajustando tu plan de alimentación según tu solicitud. Esto tomará unos segundos.",
            "update_failed": "Lo siento, no pude actualizar el plan de alimentación. Por favor, inténtalo de nuevo más tarde.",
            "no_plan": "Aún no tienes un plan de alimentación activo. Escribe 'dieta' para crear uno nuevo.",
            "approval_success": "✅ ¡Excelente! Estoy preparando la versión completa de tu plan de alimentación con recetas detalladas y lista de compras. Esto tomará unos minutos.",
            "approval_error": "Lo siento, hubo un error al procesar tu aprobación. Por favor, inténtalo de nuevo.",
            "disapproval": "Entiendo. Por favor, dime qué te gustaría cambiar en el plan. Por ejemplo: 'Cambiar el almuerzo del lunes' o 'Quiero más proteínas'."
        },
        "shopping": {
            "generating": "🛒 Comenzando a generar lista de compras basada en tu plan de alimentación. Esto tomará unos segundos...",
            "error": "Lo siento, ha ocurrido un error al crear la lista de compras. Inténtalo de nuevo más tarde.",
            "product_marked": "✅ ¡Excelente! He marcado '{product}' como comprado.",
            "product_not_found": "No encontré '{product}' en tu lista de compras. Verifica el nombre del producto o escribe 'lista de compras' para ver la lista completa."
        },
        "tracking": {
            "weight_recorded": "✅ ¡Excelente! He registrado tu peso: {weight} kg.",
            "water_recorded": "💧 ¡Excelente! He registrado tu consumo de agua: {amount} vasos (~{ml_amount} ml).",
            "weight_progress": "📉 Desde el inicio ya has perdido {weight_change:.1f} kg ({percentage:.1f}% de tu peso inicial)",
            "weight_goal_remaining": "🎯 Te faltan {remaining:.1f} kg para alcanzar tu peso objetivo de {target} kg",
            "compliance_recorded": "Se ha registrado tu cumplimiento del plan alimenticio.",
            "invalid_meal_type": "Por favor, especifica un tipo de comida válido: desayuno, almuerzo, cena o merienda."
        },
        "reminders": {
            "weight": "⚖️ ¡Hola! No olvides registrar tu peso hoy. Esto ayudará a seguir tu progreso. Simplemente escribe 'peso XX', donde XX es tu peso en kilogramos.\n\n📊 Para ver tu progreso completo, escribe 'estadísticas' o 'progreso'.",
            "water": "💧 ¡No olvides beber agua! Envía 'agua X', donde X es el número de vasos que has bebido.\n\n📊 Para ver tus estadísticas completas, escribe 'estadísticas'.",
            "weekly_report": "📊 Aquí está tu informe semanal:\n{progress}\n\n¡Excelente trabajo! ¡Sigue así! 💪"
        },
        "help": "Aquí están los comandos disponibles:"
    },
    "ru": {  # Русский
        "greeting": "👋 Привет! Добро пожаловать в GuateFit - твой персональный ассистент для похудения.",
        "onboarding": {
            "welcome": "Я помогу тебе создать план питания, адаптированный под тебя, учитывая местные продукты и твой бюджет. Давай начнем настройку!",
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
            "budget": "Какой у тебя недельный бюджет на продукты питания (в кетцалях)?",
            "completed": "🎉 Поздравляю! Ты завершил(а) настройку. Теперь ты можешь использовать команды, такие как 'план', 'статистика', 'вес XX', 'вода X', чтобы взаимодействовать с GuateFit."
        },
        "diet": {
            "common": {
                "day_format": "%d.%m.%Y",
                "weekday_names": {
                    "monday": "Понедельник",
                    "tuesday": "Вторник",
                    "wednesday": "Среда",
                    "thursday": "Четверг",
                    "friday": "Пятница",
                    "saturday": "Суббота",
                    "sunday": "Воскресенье"
                },
                "meal_types": {
                    "breakfast": "Завтрак",
                    "lunch": "Обед",
                    "dinner": "Ужин",
                    "snack": "Перекус"
                },
                "meal_emojis": {
                    "breakfast": "🍳",
                    "lunch": "🍲",
                    "dinner": "🍽️",
                    "snack": "🥪"
                }
            },
            'full': {
                "summary": {
                    "header": "*📋 ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n",
                    "deficit": "🔥 *Расчетный дефицит калорий:* \n{deficit}\n\n",
                    "proficit": "🔥 *Расчетный профицит калорий:* \n{proficit}\n\n",
                    "recommendations": "📝 *Общие рекомендации:* \n{recommendations}\n\n",
                    "price": "💰 *Примерная стоимость:* \n{price} {currency} в неделю\n\n",
                    "day_menu_example": "📅 *Пример меню на {day_name}, {date_formatted}:*\n",
                    "meal_format": "{emoji} *{meal_type}*: \n{title} {relevance}\n",
                    "calories_format": "  Калории: {calories} ккал\n",
                    "why_recommended": "  _Почему рекомендуем: {why_recommended}_\n"
                },
                "plan": {
                    "header": "*📋 ПОЛНЫЙ ПЛАН ПИТАНИЯ НА НЕДЕЛЮ*\n\n",
                    "day_header": "*📅 {day_name}, {date_formatted}*\n",
                    "total_calories": "Всего калорий: {calories} ккал\n",
                    "macro_ratio": "Соотношение БЖУ: {ratio}\n",
                    "macros": "Белки: {proteins}г, Жиры: {fats}г, Углеводы: {carbs}г\n",
                    "meal_header": "{emoji} *{meal_type}*: {title} {relevance}\n",
                    "nutrient_info": "  {nutrients}\n",
                    "why_recommended": "  _Почему: {why_recommended}_\n",
                    "day_tip": "💡 *Совет дня:* {tip}\n",
                    "commands_message": """*📱 Команды для взаимодействия с планом:*
- Напиши 'полный план' для просмотра плана на всю неделю
- Напиши 'план на сегодня' или 'меню на сегодня' для детального плана на сегодня
- Напиши 'список покупок' для получения списка продуктов
- Напиши 'выполнено/частично/заменил/пропустил завтрак/обед/ужин/перекус' для отметки о соблюдении плана
"""
                },
                "created": "🎉 Твой план питания готов! Я подобрал блюда с учетом твоих параметров и предпочтений. Просмотри план и дай мне знать, если хочешь что-то изменить.\n\n📊 Чтобы увидеть свою статистику и прогресс, напиши 'статистика' или 'прогресс' в любое время.",
                "updating": "Я корректирую твой план питания согласно запросу. Это займет несколько секунд.",
                "update_failed": "Извини, не удалось обновить план питания. Попробуй позже.",
                "no_plan": "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана.",
                "creating_error": "Ошибка при создании полного плана питания. Попробуйте позже.",
            },
            'short': {
                "summary": {
                    "header": "*📋 ПЛАН ПИТАНИЯ НА НЕДЕЛЮ (краткая версия)*\n\n",
                    "info": "Это краткая версия плана для согласования. После вашего подтверждения я подготовлю полную версию с подробными рецептами и списком покупок.\n\n",
                    "weekday": "*📅 {weekday_name}*\n",
                    "total_calories": "Всего калорий: {calories} ккал\n",
                    "meal_format": "{emoji} *{meal_type}*: {title}",
                    "meal_calories": " ({calories} ккал)",
                },
                "created": "🎉 Твой план питания готов! Я подобрал блюда с учетом твоих параметров и предпочтений.",
                "updating": "Я корректирую твой план питания согласно запросу. Это займет несколько секунд.",
                "update_failed": "Извини, не удалось обновить план питания. Попробуй позже.",
                "no_plan": "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана.",
                "creating_error": "Ошибка при создании плана питания. Попробуйте позже.",
                "approval_success": "✅ Отлично! Я готовлю полную версию твоего плана питания с подробными рецептами и списком покупок. Это займет несколько минут.",
                "approval_error": "Извини, произошла ошибка при обработке твоего согласия. Пожалуйста, попробуй еще раз.",
                "disapproval": "Понятно. Пожалуйста, скажи, что именно ты хотел бы изменить в плане. Например: 'Изменить обед в понедельник' или 'Хочу больше белка'.",

                "next_step": {
                    "header": "*👆 Это краткая версия плана. В полной версии будут:*\n",
                    "recipes": "• Подробные рецепты и инструкции по приготовлению\n",
                    "nutrition": "• Информация о питательных веществах для каждого блюда\n",
                    "explanations": "• Объяснения, почему каждое блюдо рекомендовано именно вам\n",
                    "shopping": "• Список покупок с учетом того, что у вас уже есть\n\n",
                },
                "conformation": """Пожалуйста, подтвердите план или запросите изменения:\n
    - Напишите "согласен", "ок" или "да", чтобы подтвердить план
    - Или укажите, что именно вы хотели бы изменить, например:
      "Замени обед во вторник"
      "Не хочу рыбу в понедельник"
      "Больше белка в завтраках"
    
    После вашего подтверждения я подготовлю полную версию плана
    """,
            },
            "day": {
                "header": "*📅 ПЛАН ПИТАНИЯ НА {day_name}, {date_formatted}*\n\n",
                "total_calories": "*Всего калорий:* {calories} ккал\n",
                "macro_ratio": "*Соотношение БЖУ:* {ratio}\n",
                "macros": "*Макронутриенты:* Белки: {proteins}г, Жиры: {fats}г, Углеводы: {carbs}г\n",
                "meal_header": "{emoji} *{meal_type}*: {title} {relevance}\n",
                "ingredients_header": "  *Ингредиенты:*\n",
                "ingredient_format": "  • {name}: {quantity} {unit}\n",
                "nutrition_header": "  *Пищевая ценность:*\n",
                "calories": "  • Калории: {calories} ккал\n",
                "proteins": "  • Белки: {proteins}г\n",
                "fats": "  • Жиры: {fats}г\n",
                "carbs": "  • Углеводы: {carbs}г\n",
                "fiber": "  • Клетчатка: {fiber}г\n",
                "why_recommended_header": "  *Почему рекомендуем:*\n  _{why_recommended}_\n",
                "preparation_header": "  *Способ приготовления:*\n  {preparation}\n",
                "tip": "💡 *Совет дня:* {tip}\n\n",
                "tracking": {
                    "header": "*📱 Отметьте выполнение плана:*\n",
                    "followed": "• Напишите 'выполнено завтрак/обед/ужин/перекус' для отметки о соблюдении\n",
                    "partially": "• Напишите 'частично завтрак/обед/ужин/перекус' если следовали плану частично\n",
                    "substituted": "• Напишите 'заменил завтрак/обед/ужин/перекус' если заменили блюдо\n",
                    "skipped": "• Напишите 'пропустил завтрак/обед/ужин/перекус' если пропустили прием пищи\n",
                },
                "no_plan": "К сожалению, на указанную дату нет плана питания.",
                "creating_error": "Ошибка при создании плана питания на день. Попробуйте позже."
            },
        },
        "shopping": {
            "header": "*🛒 СПИСОК ПОКУПОК*\n\n",
            "category_format": "*{category}:*\n",
            "item_format": "• {item}\n",
            "total_price": "*Общая стоимость:* ~{price} кетцалей\n\n",
            "instructions": "Отправьте 'купил [название продукта]' чтобы отметить покупку.\n",
            "generating": "🛒 Начинаю формирование списка покупок на основе твоего плана питания. Это займет несколько секунд...",
            "error": "Извини, произошла ошибка при создании списка покупок. Попробуй позже.",
            "formatting_error": "Ошибка при форматировании списка покупок. Попробуйте позже.",
            "product_marked": "✅ Отлично! Я отметил '{product}' как купленный.",
            "product_not_found": "Я не нашел '{product}' в твоем списке покупок. Проверь название продукта или напиши 'список покупок' для просмотра полного списка.",
            "no_list": "Для твоего плана ещё не создан список покупок. Напиши 'список покупок' для его создания."
        },
        "tracking": {
            "weight_recorded": "✅ Отлично! Я записал твой вес: {weight} кг.",
            "water_recorded": "💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл).",
            "weight_progress": "📉 С начала ты уже сбросил(а) {weight_change:.1f} кг ({percentage:.1f}% от начального веса)",
            "weight_goal_remaining": "🎯 До целевого веса осталось: {remaining:.1f} кг (цель: {target} кг)",
            "compliance_recorded": "Соблюдение плана питания записано.",
            "invalid_meal_type": "Пожалуйста, укажи корректный тип приема пищи: завтрак, обед, ужин или перекус."
        },
        "reminders": {
            "weight": "⚖️ Привет! Не забудь записать свой вес сегодня. Это поможет отслеживать прогресс. Просто напиши 'вес XX', где XX - твой вес в килограммах.\n\n📊 Чтобы увидеть полный прогресс, напиши 'статистика' или 'прогресс'.",
            "water": "💧 Не забывай пить воду! Отправь 'вода X', где X - количество стаканов, которые ты выпил(а).\n\n📊 Чтобы увидеть полную статистику, напиши 'статистика'.",
            "weekly_report": "📊 Вот твой еженедельный отчет:\n{progress}\n\nОтличная работа! Продолжай в том же духе! 💪"
        },
        "help_commands_list": """*📱 ДОСТУПНЫЕ КОМАНДЫ:\n
• *план*: Показывает краткую сводку вашего текущего плана питания\n
• *план на сегодня*: Показывает детальный план питания на сегодня\n
• *полный план*: Показывает полный план питания на все дни\n
• *список покупок*: Генерирует список необходимых продуктов для плана питания\n\n
• *купил [продукт]*: Отмечает продукт как купленный в списке покупок\n
• *вес XX*: Записывает ваш текущий вес (XX - число в кг)\n
• *вода X*: Записывает потребление воды (X - число стаканов)\n
• *выполнено [прием пищи]*: Отмечает прием пищи как полностью соблюденный (завтрак/обед/ужин/перекус)\n
• *частично [прием пищи]*: Отмечает прием пищи как частично соблюденный\n
• *заменил [прием пищи]*: Отмечает, что прием пищи был заменен другим блюдом\n
• *пропустил [прием пищи]*: Отмечает пропущенный прием пищи\n
• *диета*: Начинает процесс создания нового плана питания\n
• *статистика*: Показывает статистику веса, воды и соблюдения плана\n
• *прогресс*: Показывает ваш прогресс в достижении целевого веса\n
• *помощь*:"Показывает список доступных команд\n
• *изменить план*: Вы можете запросить изменение в своем плане питания, например: 'измени план на завтра, добавь больше белка'\n
""",
        "common": {
            "weekday_names": {
                "monday": "Понедельник",
                "tuesday": "Вторник",
                "wednesday": "Среда",
                "thursday": "Четверг",
                "friday": "Пятница",
                "saturday": "Суббота",
                "sunday": "Воскресенье"
            },
            "meal_types": {
                "breakfast": "Завтрак",
                "lunch": "Обед",
                "dinner": "Ужин",
                "snack": "Перекус"
            },
            "meal_emojis": {
                "breakfast": "🍳",
                "lunch": "🍲",
                "dinner": "🍽️",
                "snack": "🥪"
            }
        }
    }
}

"""
Общие шаблоны промптов для различных задач
"""

def create_whatsapp_greeting():
    """
    Создает приветственное сообщение для нового пользователя
    
    Returns:
        str: Текст приветствия
    """
    return """👋 ¡Hola! Bienvenido a GuateFit - tu asistente personal para perder peso.

Te ayudaré a crear un plan de alimentación adaptado a ti, teniendo en cuenta los productos locales y tu presupuesto.

¡Comencemos con la configuración!

¿Cómo te llamas?"""

def create_onboarding_messages():
    """
    Создает сообщения для каждого шага онбординга
    
    Returns:
        dict: Словарь с сообщениями по шагам
    """
    return {
        "name": "¿Cómo te llamas?",
        
        "age": "¿Cuántos años tienes?",
        
        "gender": """¿Cuál es tu sexo? (masculino/femenino/otro):""",
        
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
        
        "budget": "¿Cuál es tu presupuesto semanal para alimentos (en quetzales)?"
    }

def create_reminder_templates():
    """
    Создает шаблоны сообщений для напоминаний
    
    Returns:
        dict: Словарь с шаблонами напоминаний
    """
    return {
        "welcome": "👋 ¡Hola! Bienvenido a GuateFit - tu asistente personal para perder peso. Te ayudaré a crear un plan de alimentación adaptado a ti, teniendo en cuenta los productos locales y tu presupuesto. ¡Comencemos con la configuración! ¿Cómo te llamas?",
        
        "diet_created": "🎉 ¡Tu plan de alimentación está listo! He seleccionado platos teniendo en cuenta tus parámetros y preferencias. Revisa el plan y hazme saber si quieres cambiar algo.",
        
        "weight_reminder": "⚖️ ¡Hola! No olvides registrar tu peso hoy. Esto ayudará a seguir tu progreso. Simplemente escribe 'peso XX', donde XX es tu peso en kilogramos.",
        
        "water_reminder": "💧 ¡No olvides beber agua! Envía 'agua X', donde X es el número de vasos que has bebido.",
        
        "weekly_report": "📊 Aquí está tu informe semanal:\n{progress}\n\n¡Excelente trabajo! ¡Sigue así! 💪"
    }

def create_progress_message_template():
    """
    Создает шаблон сообщения о прогрессе
    
    Returns:
        str: Шаблон сообщения
    """
    return """🎉 ¡Felicitaciones! ¡Has alcanzado un nuevo hito en tu progreso!

{progress_details}

{weight_change}

📊 ¡Has completado el {progress_percentage:.1f}% de tu objetivo!
🎯 Todavía faltan {remaining_weight:.1f} kg para alcanzar tu peso objetivo de {target_weight} kg.

¡Sigue así! 💪"""

def create_water_goal_message():
    """
    Создает сообщение о достижении цели по воде
    
    Returns:
        str: Текст сообщения
    """
    return """💧 ¡Felicitaciones! ¡Has alcanzado tu objetivo diario de consumo de agua!

Continúa bebiendo agua durante el día para mantener la hidratación. Esto ayuda con la sensación de saciedad y la salud general."""

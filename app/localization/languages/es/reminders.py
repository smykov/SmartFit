# app/localization/languages/es/reminders.py
from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля напоминаний
strings = {
    'greeting': LocalizationString('👋 Hola'),

    'type': {
        'onboarding': LocalizationString('onboarding'),
        'weight': LocalizationString('weight'),
        'water': LocalizationString('water'),
        'breakfast': LocalizationString('breakfast'),
        'lunch': LocalizationString('lunch'),
        'dinner': LocalizationString('dinner'),
        'weekly_report': LocalizationString('weekly_report'),
        'plan_approval': LocalizationString('plan_approval'),
    },

    'weight': LocalizationString(
        '⚖️ ¡Hola! No olvides registrar tu peso hoy. Esto ayuda a seguir tu progreso. Simplemente escribe \'peso XX\', donde XX es tu peso en kilogramos.\n\n📊 Para ver el progreso completo, escribe \'estadísticas\' o \'progreso\'.'
    ),

    'water': LocalizationString(
        '💧 ¡No olvides beber agua! Envía \'agua X\', donde X es el número de vasos que has bebido.\n\n📊 Para ver estadísticas completas, escribe \'estadísticas\'.'
    ),

    'breakfast': LocalizationString('🍳 ¡Buenos días! No olvides marcar tu desayuno hoy.'),

    'lunch': LocalizationString('🍲 ¡Es hora de almorzar! No olvides marcar tu almuerzo hoy.'),

    'dinner': LocalizationString('🍽️ ¡Buenas noches! No olvides marcar tu cena hoy.'),

    'plan_approval': {
        'initial': LocalizationString(
            '👋 Te recordamos que tienes un plan de comidas esperando tu aprobación. ¿Quieres revisarlo ahora?'
        ),
        'same_day': LocalizationString(
            '👋 Todavía tienes un plan de comidas esperando tu aprobación desde hoy. ¿Quieres revisarlo ahora?'
        ),
        'days': LocalizationString(
            '👋 Tienes un plan de comidas que ha estado esperando tu aprobación durante {days} días. ¿Quieres revisarlo ahora?'
        ),
    },

    'onboarding': {
        'name': LocalizationString(
            'Necesitamos tu nombre para continuar la configuración. Por favor, dinos cómo deberíamos dirigirnos a ti.'
        ),
        'basic_info': LocalizationString(
            'Continuemos con la configuración. Necesitamos información básica sobre ti para un plan de comidas personalizado.'
        ),
        'weight_info': LocalizationString(
            'Necesitamos información sobre tu peso para configurar un plan de comidas. Continuemos desde donde lo dejamos.'
        ),
        'almost_complete': LocalizationString(
            '¡Ya casi terminas la configuración! Solo faltan algunas preguntas más para completar tu perfil.'
        ),
        'default': LocalizationString(
            'Continuemos con el registro para crear tu plan de comidas personalizado.'
        ),
    },
}

# Создаем модуль локализации
module = LocalizationModule(strings)
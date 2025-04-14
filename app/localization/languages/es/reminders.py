from app.localization.base import LocalizationString, LocalizationModule

# Строки для напоминаний
strings = {
    'greeting': LocalizationString('👋 ¡Hola'),
    'type.onboarding': LocalizationString('onboarding'),
    'type.weight': LocalizationString('weight'),
    'type.water': LocalizationString('water'),
    'type.breakfast': LocalizationString('breakfast'),
    'type.lunch': LocalizationString('lunch'),
    'type.dinner': LocalizationString('dinner'),
    'type.weekly_report': LocalizationString('weekly_report'),
    'type.plan_approval': LocalizationString('plan_approval'),

    'weight': LocalizationString(
        '⚖️ ¡Hola! No olvides registrar tu peso hoy. Esto ayudará a seguir tu progreso. Simplemente escribe \'peso XX\', donde XX es tu peso en kilogramos.\n\n📊 Para ver tu progreso completo, escribe \'estadísticas\' o \'progreso\'.'),
    'water': LocalizationString(
        '💧 ¡No olvides beber agua! Envía \'agua X\', donde X es el número de vasos que has bebido.\n\n📊 Para ver tus estadísticas completas, escribe \'estadísticas\'.'),
    'breakfast': LocalizationString('🍳 ¡Buenos días! No olvides registrar tu desayuno hoy.'),
    'lunch': LocalizationString('🍲 ¡Es hora del almuerzo! No olvides registrar tu almuerzo hoy.'),
    'dinner': LocalizationString('🍽️ ¡Buenas noches! No olvides registrar tu cena hoy.'),

    'plan_approval.initial': LocalizationString(
        '👋 Solo un recordatorio de que tienes un plan de dieta esperando tu aprobación. ¿Te gustaría revisarlo ahora?'),
    'plan_approval.same_day': LocalizationString(
        '👋 Todavía tienes un plan de dieta esperando tu aprobación desde hoy. ¿Te gustaría revisarlo ahora?'),
    'plan_approval.days': LocalizationString(
        '👋 Tienes un plan de dieta que ha estado esperando tu aprobación durante {days} días. ¿Te gustaría revisarlo ahora?'),

    'onboarding.name': LocalizationString(
        'Necesitamos tu nombre para continuar con la configuración. Por favor, déjanos saber cómo llamarte.'),
    'onboarding.basic_info': LocalizationString(
        'Continuemos con tu configuración. Necesitamos información básica sobre ti para crear un plan de dieta personalizado.'),
    'onboarding.weight_info': LocalizationString(
        'Necesitamos información sobre tu peso para personalizar tu plan de dieta. Continuemos donde lo dejamos.'),
    'onboarding.almost_complete': LocalizationString(
        '¡Ya casi terminas la configuración! Solo unas pocas preguntas más para completar tu perfil.'),
    'onboarding.default': LocalizationString('Continuemos con tu registro para crear tu plan de dieta personalizado.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)
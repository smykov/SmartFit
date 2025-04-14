from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'plan_not_found': LocalizationString('Plan de dieta no encontrado'),
    'plan_approved': LocalizationString('Aprobado, generando la versión completa del plan...'),
    'plan_approval_error': LocalizationString('Se produjo un error al procesar la aprobación'),

    'full': {
        'created': LocalizationString(
            '🎉 ¡Tu plan de alimentación está listo! He seleccionado platos teniendo en cuenta tus parámetros y preferencias. Revisa el plan y hazme saber si quieres cambiar algo.'),
        'updating': LocalizationString(
            'Estoy ajustando tu plan de alimentación según tu solicitud. Esto tomará unos segundos.'),
        'update_failed': LocalizationString(
            'Lo siento, no pude actualizar el plan de alimentación. Por favor, inténtalo de nuevo más tarde.'),
        'no_plan': LocalizationString(
            'Aún no tienes un plan de alimentación activo. Escribe "dieta" para crear uno nuevo.'),
        'no_updates': LocalizationString('No se realizaron actualizaciones en el plan de alimentación.'),
        'creating_error': 'Error al crear el plan de dieta. Por favor, inténtelo de nuevo más tarde.',
        'summary': {
            'header': '*📋 PLAN DE DIETA PERSONAL*\n\n',
            'deficit': '🔥 *Déficit calórico estimado:* \n{deficit}\n\n',
            'proficit': '🔥 *Superávit calórico estimado:* \n{proficit}\n\n',
            'recommendations': '📝 *Recomendaciones generales:* \n{recommendations}\n\n',
            'price': '💰 *Costo estimado:* \n{price} {currency} por semana\n\n',
            'day_menu_example': '📅 *Menú de ejemplo para {day_name}, {date_formatted}:*\n',
            'meal_format': '{emoji} *{meal_type}*: \n{title} {relevance}\n',
            'calories_format': '  Calorías: {calories} kcal\n',
            'why_recommended': '  _Por qué se recomienda: {why_recommended}_\n'
        },
        'plan': {
            'commands_message': '''*📱 Comandos para interactuar con el plan:*
    - Escriba 'plan completo' para ver el plan de toda la semana
    - Escriba 'plan de hoy' o 'menú de hoy' para obtener un plan detallado para hoy
    - Escriba 'lista de compras' para obtener una lista de productos
    - Escriba 'completado/parcialmente/sustituido/omitido desayuno/almuerzo/cena/merienda' para marcar el cumplimiento
    '''
        }
    },
    'short': {
        'creating_error': 'Error al crear el plan de dieta breve. Por favor, inténtelo de nuevo más tarde.',
        'next_step': {
            'header': '*👆 Esta es una versión breve del plan. La versión completa incluirá:*\n',
            'recipes': '• Recetas detalladas e instrucciones de cocina\n',
            'nutrition': '• Información nutricional para cada plato\n',
            'explanations': '• Explicaciones de por qué cada plato es recomendado específicamente para usted\n',
            'shopping': '• Lista de compras teniendo en cuenta lo que ya tiene\n\n',
            'invalid_version': LocalizationString('El plan no es una versión corta'),
        }
    },
    'day': {
        'creating_error': 'Error al crear el plan de dieta diario. Por favor, inténtelo de nuevo más tarde.',
        'no_plan': 'Desafortunadamente, no hay un plan de comidas para la fecha especificada.',
        'tracking': {
            'header': '*📱 Marque la ejecución de su plan:*\n',
            'followed': '• Escriba \'completado desayuno/almuerzo/cena/merienda\' para marcar como seguido\n',
            'partially': '• Escriba \'parcialmente desayuno/almuerzo/cena/merienda\' si siguió el plan parcialmente\n',
            'substituted': '• Escriba \'sustituido desayuno/almuerzo/cena/merienda\' si reemplazó el plato\n',
            'skipped': '• Escriba \'omitido desayuno/almuerzo/cena/merienda\' si omitió la comida\n'
        }
    },
    'update': {
        "success_header": LocalizationString("✅ *Plan de alimentación actualizado*\n\n{comment}\n"),
        "day_updated_with_date": LocalizationString("\nMenú actualizado para *{day_name}, {date_formatted}*"),
        "day_updated": LocalizationString("\nMenú actualizado para *{day_name}*"),
        "unknown_day_updated": LocalizationString("\nMenú actualizado para {date_str}"),
        "formatting_error": LocalizationString(
            "Error al formatear el mensaje de actualización de la dieta. Por favor, inténtelo de nuevo."),
        "no_updates": LocalizationString(
            "No se realizaron actualizaciones en el plan de alimentación. Intente especificar qué desea cambiar."),
        'default_comment': LocalizationString('Plan de dieta actualizado según la solicitud'),
        'parsing_error': LocalizationString('No se pudo analizar la respuesta de IA'),
        'invalid_format': LocalizationString('Formato de respuesta inválido de IA'),
        'update_failed': LocalizationString('No se pudo actualizar el plan de dieta'),
    },
    'ai': {
        'ai.user_not_found': LocalizationString('Lo siento, no pude encontrar información del usuario.'),
        'ai.processing_error': LocalizationString(
            'Lo siento, ocurrió un error al procesar tu pregunta. Por favor, inténtalo de nuevo más tarde.'),
    }
}
# Создаем модуль локализации
module = LocalizationModule(strings)

from app.localization.base import LocalizationString, LocalizationModule

# Strings for commands module (Spanish)
strings = {
    # General command messages
    'general.commandNotFound': LocalizationString(
        'Comando no encontrado. Escribe "ayuda" para ver los comandos disponibles.'),
    'general.executionError': LocalizationString(
        'Se produjo un error al ejecutar el comando. Por favor, inténtalo de nuevo más tarde.'),

    # Weight command
    'weight.recorded': LocalizationString('✅ ¡Excelente! He registrado tu peso: {weight} kg.'),
    'weight.invalidFormat': LocalizationString(
        'Por favor, ingresa tu peso en el formato: "peso XX", donde XX es tu peso en kilogramos.'),
    'weight.outOfRange': LocalizationString('El valor del peso debe estar entre 30 y 300 kg.'),
    'weight.invalidValue': LocalizationString('Valor de peso no válido. Por favor, ingresa un número.'),
    'weight.error': LocalizationString(
        'Se produjo un error al registrar tu peso. Por favor, inténtalo de nuevo más tarde.'),

    # Water command
    'water.recorded': LocalizationString(
        '💧 ¡Excelente! He registrado tu consumo de agua: {amount} vasos (~{ml_amount} ml).'),
    'water.invalidFormat': LocalizationString(
        'Por favor, ingresa tu consumo de agua en el formato: "agua X", donde X es el número de vasos que has bebido.'),
    'water.outOfRange': LocalizationString('El número de vasos debe estar entre 0 y 20.'),
    'water.invalidValue': LocalizationString('Valor de consumo de agua no válido. Por favor, ingresa un número.'),
    'water.error': LocalizationString(
        'Se produjo un error al registrar tu consumo de agua. Por favor, inténtalo de nuevo más tarde.'),
    # Help command
    'help.helpText': LocalizationString('''*📱 COMANDOS DISPONIBLES:*\n
- *plan*: Muestra un resumen de tu plan de alimentación actual\n
- *plan hoy*: Muestra el plan detallado de comidas para hoy\n
- *plan completo*: Muestra el plan completo de alimentación para todos los días\n
- *lista de compras*: Genera una lista de productos necesarios para el plan de alimentación\n\n
- *comprado [producto]*: Marca un producto como comprado en la lista de compras\n
- *peso XX*: Registra tu peso actual (XX - número en kg)\n
- *agua X*: Registra el consumo de agua (X - número de vasos)\n
- *completado [comida]*: Marca una comida como completamente seguida (desayuno/almuerzo/cena/merienda)\n
- *parcialmente [comida]*: Marca una comida como parcialmente seguida\n
- *sustituido [comida]*: Marca que una comida fue reemplazada por otro plato\n
- *omitido [comida]*: Marca una comida omitida\n
- *dieta*: Inicia el proceso de creación de un nuevo plan de alimentación\n
- *estadísticas*: Muestra estadísticas de peso, agua y cumplimiento del plan\n
- *progreso*: Muestra tu progreso hacia el peso objetivo\n
- *ayuda*: Muestra una lista de comandos disponibles\n
- *actualizar plan*: Puedes solicitar un cambio en tu plan de comidas, por ejemplo: 'actualizar plan para mañana, añadir más proteína'\n
'''),

    # Diet command
    'diet.generationStarted': LocalizationString(
        '🔄 Comenzando a generar tu plan de alimentación. Esto tomará unos momentos...'),
    'diet.generationDetails': LocalizationString(
        'Crearé un plan de alimentación personalizado basado en tu perfil, preferencias y objetivos.'),
    'diet.noDietPlan': LocalizationString(
        'Aún no tienes un plan de alimentación activo. Escribe "dieta" para crear uno.'),
    'diet.noDietForToday': LocalizationString('Lo siento, no hay un plan de alimentación disponible para hoy.'),
    'diet.error': LocalizationString(
        'Se produjo un error al procesar tu plan de alimentación. Por favor, inténtalo de nuevo más tarde.'),

    # Shopping list command
    'shoppingList.generating': LocalizationString(
        '🛒 Generando lista de compras basada en tu plan de alimentación. Esto tomará unos momentos...'),
    'shoppingList.error': LocalizationString(
        'Se produjo un error al generar la lista de compras. Por favor, inténtalo de nuevo más tarde.'),
    'shoppingList.invalidProductFormat': LocalizationString(
        'Por favor, usa el formato: "compré [nombre del producto]" para marcar un producto como comprado.'),
    'shoppingList.productMarked': LocalizationString('✅ ¡Excelente! He marcado "{product}" como comprado.'),
    'shoppingList.productNotFound': LocalizationString(
        'No pude encontrar "{product}" en tu lista de compras. Verifica el nombre o escribe "lista de compras" para ver la lista completa.'),
    'shoppingList.noDietPlan': LocalizationString(
        'Aún no tienes un plan de alimentación activo. Escribe "dieta" para crear uno.'),

    # Stats command
    'stats.error': LocalizationString(
        'Se produjo un error al generar tus estadísticas. Por favor, inténtalo de nuevo más tarde.'),
    'stats.default_message': LocalizationString(
        'Aquí están tus estadísticas actuales. Escribe "dieta" para ver tu plan actual o "ayuda" para más comandos.'),

    # Compliance command
    'compliance.invalidFormat': LocalizationString(
        'Por favor, usa el formato: "[estado] [tipo de comida]", donde estado es uno de: completado, parcialmente, sustituido, omitido.'),
    'compliance.invalidType': LocalizationString(
        'Tipo de cumplimiento desconocido. Por favor, usa uno de: completado, parcialmente, sustituido, omitido.'),
    'compliance.invalidMealType': LocalizationString(
        'Tipo de comida no válido. Por favor, especifica: desayuno, almuerzo, cena o merienda.'),
    'compliance.noDietPlan': LocalizationString('No tienes un plan de alimentación activo para rastrear comidas.'),
    'compliance.recordError': LocalizationString(
        'Se produjo un error al registrar el cumplimiento de comidas. Por favor, inténtalo de nuevo más tarde.'),
    'compliance.recorded': LocalizationString('Se ha registrado el cumplimiento para {meal_type} como {status}.'),
    'compliance.statusKeywords': LocalizationString({
        'completado': 'followed',
        'seguido': 'followed',
        'parcial': 'partially',
        'parcialmente': 'partially',
        'sustituido': 'substituted',
        'reemplazado': 'substituted',
        'omitido': 'skipped',
        'saltado': 'skipped'
    }),

    'compliance.mealTypeKeywords': LocalizationString({
        'desayuno': 'breakfast',
        'mañana': 'breakfast',
        'almuerzo': 'lunch',
        'comida': 'lunch',
        'mediodía': 'lunch',
        'cena': 'dinner',
        'noche': 'dinner',
        'merienda': 'snack',
        'bocadillo': 'snack'
    }),

    'compliance.mealTypeDisplay': LocalizationString({
        'breakfast': 'desayuno',
        'lunch': 'almuerzo',
        'dinner': 'cena',
        'snack': 'merienda'
    }),
    # Language command
    'language.languagesList': LocalizationString(
        'Idiomas disponibles:\n\n🇪🇸 Español: Escribe "idioma es"\n🇷🇺 Ruso: Escribe "idioma ru"\n🇬🇧 Inglés: Escribe "idioma en"'),
    'language.unsupportedLanguage': LocalizationString(
        'Código de idioma no compatible. Opciones disponibles: {languages}'),
    'language.unavailableService': LocalizationString('El servicio de localización no está disponible.'),
    'language.languageChanged': LocalizationString('¡Idioma cambiado a Español!'),
}

# Create localization module
module = LocalizationModule(strings)
from app.localization.base import LocalizationString, LocalizationModule

# Messaging strings
strings = {
    'invalidMessageFormat': LocalizationString('Formato de mensaje no válido'),
    'welcomeNewUser': LocalizationString('¡Bienvenido a GuateFit! Comencemos configurando tu perfil.'),
    'messageAlreadyProcessed': LocalizationString('Este mensaje ya ha sido procesado'),
    'commandNotFound': LocalizationString('Lo siento, no pude entender ese comando. Escribe "ayuda" para ver los comandos disponibles.'),
    'unknownCommand': LocalizationString('Comando desconocido: {text}'),
    'prerequisitesNotMet': LocalizationString('No se puede ejecutar este comando en este momento'),
    'processingCommand': LocalizationString('Procesando tu comando...'),
    'delayedMassage': LocalizationString('Mensaje retrasado: '),

    # Keys for message processor
    'userNotFound': LocalizationString('Usuario no encontrado'),
    'noPendingPlan': LocalizationString('No se encontró un plan de dieta pendiente'),
    'noDietPlan': LocalizationString('No tienes un plan de dieta activo. Usa el comando "dieta" para crear uno.'),
    'updatingPlan': LocalizationString('Actualizando tu plan de dieta...'),
    'updateFailed': LocalizationString('No se pudo actualizar el plan de dieta. Por favor, inténtalo de nuevo.'),

}

# Create localization module
module = LocalizationModule(strings)
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
}

# Create localization module
module = LocalizationModule(strings)
from app.localization.base import LocalizationString, LocalizationModule

# Messaging strings
strings = {
    'invalidMessageFormat': LocalizationString('Invalid message format'),
    'welcomeNewUser': LocalizationString('Welcome to GuateFit! Let\'s start by setting up your profile.'),
    'messageAlreadyProcessed': LocalizationString('This message has already been processed'),
    'commandNotFound': LocalizationString('Sorry, I couldn\'t understand that command. Type "help" to see available commands.'),
    'unknownCommand': LocalizationString('Unknown command: {text}'),
    'prerequisitesNotMet': LocalizationString('Cannot execute this command at the moment'),
    'processingCommand': LocalizationString('Processing your command...'),
}

# Create localization module
module = LocalizationModule(strings)
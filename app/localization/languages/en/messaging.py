from app.localization.base import LocalizationString, LocalizationModule

# Messaging strings
strings = {
    'invalidMessageFormat': LocalizationString('Invalid message format'),
    'welcomeNewUser': LocalizationString('Welcome to SmartFit! Let\'s start by setting up your profile.'),
    'messageAlreadyProcessed': LocalizationString('This message has already been processed'),
    'commandNotFound': LocalizationString('Sorry, I couldn\'t understand that command. Type "help" to see available commands.'),
    'unknownCommand': LocalizationString('Unknown command: {text}'),
    'prerequisitesNotMet': LocalizationString('Cannot execute this command at the moment'),
    'processingCommand': LocalizationString('Processing your command...'),
    'delayedMassage': LocalizationString('Delayed message: '),

    # Keys for message processor
    'userNotFound': LocalizationString('User not found'),
    'noPendingPlan': LocalizationString('No pending diet plan found'),
    'noDietPlan': LocalizationString('You don\'t have an active diet plan. Use "diet" command to create one.'),
    'updatingPlan': LocalizationString('Updating your diet plan...'),
    'updateFailed': LocalizationString('Failed to update diet plan. Please try again.'),
}

# Create localization module
module = LocalizationModule(strings)
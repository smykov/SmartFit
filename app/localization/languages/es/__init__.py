from app.localization.base import LanguageBase

from app.localization.languages.es import common
from app.localization.languages.es import commands
from app.localization.languages.es import onboarding
# Импортируем другие модули когда они будут созданы
# from app.localization.languages.es import diet
# from app.localization.languages.es import tracking
# from app.localization.languages.es import errors

# Создаем экземпляр языка
language = LanguageBase()

# Регистрируем все модули
language.register_module('common', common.module)
language.register_module('commands', commands.module)
language.register_module('onboarding', onboarding.module)
# Регистрируем другие модули когда они будут созданы
# language.register_module('diet', diet.module)
# language.register_module('tracking', tracking.module)
# language.register_module('errors', errors.module)
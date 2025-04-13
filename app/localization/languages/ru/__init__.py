from app.localization.base import LanguageBase

from app.localization.languages.ru import common
from app.localization.languages.ru import commands
from app.localization.languages.ru import onboarding
# Импортируем другие модули когда они будут созданы
# from app.localization.languages.ru import diet
# from app.localization.languages.ru import tracking
# from app.localization.languages.ru import errors

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
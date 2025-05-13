# app/localization/languages/ru/__init__.py
from app.localization.base import LanguageBase

# Импортируем все модули
from app.localization.languages.ru import common
from app.localization.languages.ru import commands
from app.localization.languages.ru import diet
from app.localization.languages.ru import onboarding
from app.localization.languages.ru import tracking
from app.localization.languages.ru import shopping
from app.localization.languages.ru import messaging
from app.localization.languages.ru import errors
from app.localization.languages.ru import reminders
from app.localization.languages.ru import user

# Создаем экземпляр языка
language = LanguageBase()

# Регистрируем все модули
language.register_module('common', common.module)
language.register_module('commands', commands.module)
language.register_module('diet', diet.module)
language.register_module('onboarding', onboarding.module)
language.register_module('tracking', tracking.module)
language.register_module('shopping', shopping.module)
language.register_module('messaging', messaging.module)
language.register_module('errors', errors.module)
language.register_module('reminders', reminders.module)
language.register_module('user', user.module)

# Проверка структуры языка (для диагностики)
print(f"Russian language initialized with modules: {list(language.modules.keys())}")
for module_name, module in language.modules.items():
    print(f"Module '{module_name}' registered with keys: {list(module.strings.keys())}")
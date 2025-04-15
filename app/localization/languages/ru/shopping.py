from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'shopping': {
        'header': LocalizationString('*🛒 СПИСОК ПОКУПОК*\n\n'),
        'generating': LocalizationString(
            '🛒 Начинаю формирование списка покупок на основе твоего плана питания. Это займет несколько секунд...'),
        'error': LocalizationString('Извини, произошла ошибка при создании списка покупок. Попробуй позже.'),
        'product_marked': LocalizationString('✅ Отлично! Я отметил \'{product}\' как купленный.'),
        'product_not_found': LocalizationString(
            'Я не нашел \'{product}\' в твоем списке покупок. Проверь название продукта или напиши "список покупок" для просмотра полного списка.'),
        'item_info_format': LocalizationString('{name}: {quantity} {unit}'),
        'price_format': LocalizationString(' (~{price} к.)'),
        'purchased_item_format': LocalizationString('✅ {item}'),
        'items_count': LocalizationString(
            'В вашем списке покупок {count} наименований.\n\n',
            plural_forms={
                'one': 'В вашем списке покупок {count} наименование.\n\n',
                'few': 'В вашем списке покупок {count} наименования.\n\n',
                'many': 'В вашем списке покупок {count} наименований.\n\n'
            }
        ),
        'category_with_count_format': LocalizationString(
            '*{category}* ({count} наименований):\n',
            plural_forms={
                'one': '*{category}* ({count} наименование):\n',
                'few': '*{category}* ({count} наименования):\n',
                'many': '*{category}* ({count} наименований):\n'
            }
        ),
        'categories': {
            'fruits_vegetables': LocalizationString('Фрукты и овощи'),
            'meat_fish': LocalizationString('Мясо и рыба'),
            'dairy': LocalizationString('Молочные продукты'),
            'bread_cereals': LocalizationString('Хлеб и крупы'),
            'spices': LocalizationString('Специи и приправы'),
            'drinks': LocalizationString('Напитки'),
            'other': LocalizationString('Другое'),
        },
        'shopping_progress': LocalizationString(
            'Прогресс покупок: {purchased}/{total} куплено ({percentage}%).\n'
            'Осталось купить {remaining} наименований.\n\n',
            plural_forms={
                'one': 'Прогресс покупок: {purchased}/{total} куплено ({percentage}%).\n'
                       'Осталось купить {remaining} наименование.\n\n',
                'few': 'Прогресс покупок: {purchased}/{total} куплено ({percentage}%).\n'
                       'Осталось купить {remaining} наименования.\n\n',
                'many': 'Прогресс покупок: {purchased}/{total} куплено ({percentage}%).\n'
                        'Осталось купить {remaining} наименований.\n\n',
                'zero': 'Прогресс покупок: {purchased}/{total} куплено ({percentage}%).\n'
                        'Все продукты куплены!\n\n'
            }
        ),
        'diet_plan_not_found': LocalizationString('План питания не найден'),
        'parsing_error': LocalizationString('Не удалось обработать ответ для списка покупок'),
        'save_failed': LocalizationString('Не удалось сохранить список покупок в базе данных'),
        'generating_error': LocalizationString('Ошибка при создании списка покупок'),
        'marking_error': LocalizationString('Ошибка при отметке продукта как купленного'),
        'no_diet_plan': LocalizationString('У вас еще нет активного плана питания. Напишите "диета" для его создания.'),
        'no_list': LocalizationString(
            'Не найден список покупок для вашего текущего плана питания. Напишите "список покупок" для его создания.'),
    }
}

# Создаем модуль локализации
module = LocalizationModule(strings)
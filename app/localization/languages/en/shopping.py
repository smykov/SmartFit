from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'item_info_format': LocalizationString('{name}: {quantity} {unit}'),
    'price_format': LocalizationString(' (~{price} q.)'),
    'purchased_item_format': LocalizationString('✅ {item}'),
    'items_count': LocalizationString(
        'Your shopping list contains {count} items.\n\n',
        plural_forms={
            'one': 'Your shopping list contains {count} item.\n\n',
            'few': 'Your shopping list contains {count} items.\n\n',
            'many': 'Your shopping list contains {count} items.\n\n'
        }
    ),
    'category_with_count_format': LocalizationString(
        '*{category}* ({count} items):\n',
        plural_forms={
            'one': '*{category}* ({count} item):\n',
            'few': '*{category}* ({count} items):\n',
            'many': '*{category}* ({count} items):\n'
        }
    ),
    'categories.fruits_vegetables': LocalizationString('Fruits and Vegetables'),
    'categories.meat_fish': LocalizationString('Meat and Fish'),
    'categories.dairy': LocalizationString('Dairy'),
    'categories.bread_cereals': LocalizationString('Bread and Cereals'),
    'categories.spices': LocalizationString('Spices'),
    'categories.drinks': LocalizationString('Drinks'),
    'categories.other': LocalizationString('Other'),
    'shopping_progress': LocalizationString(
        'Shopping progress: {purchased}/{total} items purchased ({percentage}%).\n'
        'You still need to buy {remaining} items.\n\n',
        plural_forms={
            'one': 'Shopping progress: {purchased}/{total} items purchased ({percentage}%).\n'
                   'You still need to buy {remaining} item.\n\n',
            'zero': 'Shopping progress: {purchased}/{total} items purchased ({percentage}%).\n'
                    'All items have been purchased!\n\n'
        }
    ),
    'diet_plan_not_found': LocalizationString('Diet plan not found'),
    'parsing_error': LocalizationString('Failed to parse shopping list response'),
    'save_failed': LocalizationString('Failed to save shopping list to database'),
    'generating_error': LocalizationString('Error generating shopping list'),
    'marking_error': LocalizationString('Error marking product as purchased'),
    'no_diet_plan': LocalizationString('You don\'t have an active diet plan yet. Type "diet" to create one.'),
    'no_list': LocalizationString(
        'No shopping list found for your current diet plan. Type "shopping list" to create one.'),

    'header': LocalizationString('*🛒 SHOPPING LIST*\n\n'),
    'generating': LocalizationString(
        '🛒 Generating shopping list based on your diet plan. This will take a few seconds...'),
    'error': LocalizationString('Sorry, there was an error creating your shopping list. Please try again later.'),
    'product_marked': LocalizationString('✅ Great! I\'ve marked \'{product}\' as purchased.'),
    'product_not_found': LocalizationString(
        'I couldn\'t find \'{product}\' in your shopping list. Check the product name or type "shopping list" to see the full list.'),

}
# Создаем модуль локализации
module = LocalizationModule(strings)
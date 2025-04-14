from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'shopping.item_info_format': LocalizationString('{name}: {quantity} {unit}'),
    'shopping.price_format': LocalizationString(' (~{price} q.)'),
    'shopping.purchased_item_format': LocalizationString('✅ {item}'),
    'shopping.items_count': LocalizationString(
        'Su lista de compras contiene {count} artículos.\n\n',
        plural_forms={
            'one': 'Su lista de compras contiene {count} artículo.\n\n',
            'few': 'Su lista de compras contiene {count} artículos.\n\n',
            'many': 'Su lista de compras contiene {count} artículos.\n\n'
        }
    ),
    'shopping.category_with_count_format': LocalizationString(
        '*{category}* ({count} artículos):\n',
        plural_forms={
            'one': '*{category}* ({count} artículo):\n',
            'few': '*{category}* ({count} artículos):\n',
            'many': '*{category}* ({count} artículos):\n'
        }
    ),
    'shopping.categories.fruits_vegetables': LocalizationString('Frutas y verduras'),
    'shopping.categories.meat_fish': LocalizationString('Carne y pescado'),
    'shopping.categories.dairy': LocalizationString('Lácteos'),
    'shopping.categories.bread_cereals': LocalizationString('Pan y cereales'),
    'shopping.categories.spices': LocalizationString('Especias'),
    'shopping.categories.drinks': LocalizationString('Bebidas'),
    'shopping.categories.other': LocalizationString('Otros'),
    'shopping.shopping_progress': LocalizationString(
        'Progreso de compras: {purchased}/{total} artículos comprados ({percentage}%).\n'
        'Todavía necesita comprar {remaining} artículos.\n\n',
        plural_forms={
            'one': 'Progreso de compras: {purchased}/{total} artículos comprados ({percentage}%).\n'
                   'Todavía necesita comprar {remaining} artículo.\n\n',
            'zero': 'Progreso de compras: {purchased}/{total} artículos comprados ({percentage}%).\n'
                    '¡Todos los artículos han sido comprados!\n\n'
        }
    ),
    'diet_plan_not_found': LocalizationString('Plan de dieta no encontrado'),
    'parsing_error': LocalizationString('No se pudo analizar la respuesta de la lista de compras'),
    'save_failed': LocalizationString('No se pudo guardar la lista de compras en la base de datos'),
    'generating_error': LocalizationString('Error al generar la lista de compras'),
    'marking_error': LocalizationString('Error al marcar el producto como comprado'),
    'no_diet_plan': LocalizationString('Aún no tienes un plan de dieta activo. Escribe "dieta" para crear uno.'),
    'no_list': LocalizationString(
        'No se encontró una lista de compras para tu plan de dieta actual. Escribe "lista de compras" para crear una.'),

    'header': LocalizationString('*🛒 LISTA DE COMPRAS*\n\n'),
    'generating': LocalizationString(
        '🛒 Comenzando a generar lista de compras basada en tu plan de alimentación. Esto tomará unos segundos...'),
    'error': LocalizationString(
        'Lo siento, ha ocurrido un error al crear la lista de compras. Inténtalo de nuevo más tarde.'),
    'product_marked': LocalizationString('✅ ¡Excelente! He marcado \'{product}\' como comprado.'),
    'product_not_found': LocalizationString(
        'No encontré \'{product}\' en tu lista de compras. Verifica el nombre del producto o escribe "lista de compras" para ver la lista completa.'),
}
# Создаем модуль локализации
module = LocalizationModule(strings)
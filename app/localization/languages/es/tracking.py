from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля трекинга (испанский)
strings = {
    # Сообщения для весовых данных
    'weight.recorded': LocalizationString('✅ ¡Excelente! He registrado tu peso: {weight} kg.'),
    'weight.progress': LocalizationString(
        '📉 Desde el principio, ya has perdido {weight_change:.1f} kg ({percentage:.1f}% de tu peso inicial)'),
    'weight.change': LocalizationString(
        '📈 Desde el principio, has ganado {weight_change:.1f} kg ({percentage:.1f}% de tu peso inicial)'),
    'weight.goal_remaining': LocalizationString(
        '🎯 Te faltan {remaining:.1f} kg para alcanzar tu peso objetivo de {target} kg'),
    'weight.goal_percentage': LocalizationString('\n📊 ¡Has completado {percentage:.1f}% de tu objetivo!\n\n'),
    'weight.keep_tracking': LocalizationString('¡Continúa registrando tu progreso regularmente! 💪'),

    # Сообщения для воды
    'water.recorded': LocalizationString(
        '💧 ¡Excelente! He registrado tu consumo de agua: {amount} vasos (~{ml_amount} ml)'),
    'water.daily_total': LocalizationString('\nHoy has bebido en total: {current_intake} ml\n'),
    'water.goal_percentage': LocalizationString('Esto es {percentage:.1f}% de tu objetivo diario de {goal} ml\n\n'),
    'water.motivation': LocalizationString(
        '¡Sigue así! El consumo regular de agua ayuda a controlar el hambre y mejora el bienestar general.'),

    # Сообщения для соблюдения диеты
    'compliance.followed': LocalizationString('✅ ¡Excelente! {meal_type} completado según el plan.'),
    'compliance.partially': LocalizationString('⚠️ ¡Bien! {meal_type} parcialmente seguido según el plan.'),
    'compliance.substituted': LocalizationString('🔄 ¡Entendido! {meal_type} fue reemplazado por otro plato.'),
    'compliance.skipped': LocalizationString('❌ ¡Anotado! {meal_type} fue omitido.'),
    'compliance.generic_status': LocalizationString('Estado registrado para la comida: {meal_type}.'),
    'compliance.overall_score': LocalizationString('\n\nCumplimiento general del plan para hoy: {score:.1f}%'),
    'compliance.excellent': LocalizationString('\n\n👍 ¡Excelente trabajo! Continúa así.'),
    'compliance.good': LocalizationString('\n\n👍 ¡Buen resultado! Trata de seguir el plan.'),
    'compliance.keep_trying': LocalizationString('\n\n💪 ¡No te rindas! Cada día es una nueva oportunidad.'),

    # Сообщения для статистики
    'stats.header': LocalizationString('*📊 ESTADÍSTICAS Y PROGRESO*\n\n'),
    'stats.weight_section': LocalizationString('*⚖️ Progreso de peso:*\n'),
    'stats.weight_initial': LocalizationString('• Peso inicial: {weight} kg\n'),
    'stats.weight_current': LocalizationString('• Peso actual: {weight} kg\n'),
    'stats.weight_target': LocalizationString('• Peso objetivo: {weight} kg\n\n'),
    'stats.weight_change_negative': LocalizationString('• Cambio: -{change:.1f} kg 👍\n'),
    'stats.weight_change_positive': LocalizationString('• Cambio: +{change:.1f} kg\n'),
    'stats.weight_change_neutral': LocalizationString('• Cambio: 0 kg (peso estable)\n'),
    'stats.weight_goal_remaining': LocalizationString('• Restante para el objetivo: {remaining:.1f} kg\n'),
    'stats.weight.goal_percentage': LocalizationString('• Cumplimiento del objetivo: {percentage:.1f}%\n\n'),
    'stats.water_section': LocalizationString('*💧 Consumo de agua hoy:*\n'),
    'stats.water_consumed': LocalizationString('• Consumido: {intake} ml\n'),
    'stats.water_goal': LocalizationString('• Objetivo: {goal} ml\n'),
    'stats.water_percentage': LocalizationString('• Completado: {percentage:.1f}%\n\n'),
    'stats.compliance_section': LocalizationString('*🍽️ Cumplimiento del plan de comidas:*\n'),
    'stats.compliance_overall': LocalizationString('\nCumplimiento general: {score:.1f}%\n\n'),
    'stats.motivation': LocalizationString('💪 *¡Sigue así!* Estás en camino hacia tu objetivo.'),
    'stats.weekly_report_header': LocalizationString('📊 *Informe semanal de progreso para {user_name}*\n\n'),
    'stats.weight_no_data': LocalizationString('⚖️ *Peso:* No hay datos para la última semana\n'),
    'stats.water_days_tracked': LocalizationString('• Días registrados: {days}/7\n'),
    'stats.water_average': LocalizationString('• Consumo promedio: {avg:.1f} l/día\n'),
    'stats.water_excellent': LocalizationString('• Estado: ¡Excelente! Estás alcanzando tu objetivo de agua 👍\n'),
    'stats.water_good': LocalizationString('• Estado: Bien, pero podrías aumentar tu consumo de agua\n'),
    'stats.water_insufficient': LocalizationString('• Estado: Consumo insuficiente de agua, trata de beber más\n'),
    'stats.water_no_data': LocalizationString('💧 *Consumo de agua:* No hay datos para la última semana\n'),
    'stats.goal_section': LocalizationString('🎯 *Progreso hacia el objetivo:*\n'),
    'stats.goal_target': LocalizationString('• Peso objetivo: {target} kg\n'),
    'stats.goal_remaining': LocalizationString('• Restante: {remaining:.1f} kg\n'),
    'stats.goal_percentage': LocalizationString('• Progreso: {percentage:.1f}% completado\n'),
    'stats.report_error': LocalizationString('El informe semanal no está disponible. Por favor, inténtalo más tarde.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)
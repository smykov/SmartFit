# app/localization/languages/es/onboarding.py
from app.localization.base import LocalizationString, LocalizationModule

# Strings for onboarding module (Spanish)
strings = {
    # Welcome and basic onboarding messages
    'welcome': LocalizationString(
        '👋 ¡Bienvenido a GuateFit - tu asistente personal para perder peso! Te ayudaré a crear un plan de alimentación personalizado según tus preferencias, productos locales y presupuesto.'),
    'nameRequest': LocalizationString('¿Cómo te llamas?'),
    'nameRequestExample': LocalizationString('Por ejemplo: Juan'),
    'ageRequest': LocalizationString('¿Cuántos años tienes?'),
    'ageRequestExample': LocalizationString('Por ejemplo: 30'),
    'genderRequest': LocalizationString('¿Cuál es tu género? (masculino/femenino/otro):'),
    'genderRequestExample': LocalizationString('Por ejemplo: masculino'),
    'heightRequest': LocalizationString('¿Cuál es tu altura en centímetros?'),
    'heightRequestExample': LocalizationString('Por ejemplo: 175'),
    'currentWeightRequest': LocalizationString('¿Cuánto pesas actualmente en kilogramos?'),
    'currentWeightRequestExample': LocalizationString('Por ejemplo: 80'),
    'targetWeightRequest': LocalizationString('¿Qué peso quieres alcanzar (en kilogramos)?'),
    'targetWeightRequestExample': LocalizationString('Por ejemplo: 70'),
    'activityLevelRequest': LocalizationString("""Evalúa tu nivel de actividad física:
1. Estilo de vida sedentario (poca o ninguna actividad física)
2. Actividad ligera (ejercicios ligeros 1-3 veces por semana)
3. Actividad moderada (ejercicios moderados 3-5 veces por semana)
4. Actividad alta (entrenamientos intensivos 6-7 veces por semana)
5. Actividad muy alta (trabajo físico o 2 entrenamientos al día)

Responde con un número o dímelo con tus propias palabras:"""),
    'activityLevelRequestExample': LocalizationString('Por ejemplo: 3 o "actividad moderada"'),
    'weightGoalRequest': LocalizationString("""¿Cuál es tu objetivo de peso?
1. Perder peso
2. Mantener tu peso actual
3. Ganar peso

Responde con un número o dímelo con tus propias palabras:"""),
    'weightGoalRequestExample': LocalizationString('Por ejemplo: 1 o "perder peso"'),
    'dietPreferenceRequest': LocalizationString("""¿Qué preferencias alimentarias tienes?
1. Dieta regular (sin restricciones)
2. Vegetariana (sin carne, pero con huevos y lácteos)
3. Vegana (solo alimentos vegetales)
4. Baja en carbohidratos (restricción de carbohidratos)
5. Keto (alto contenido de grasas, muy bajo en carbohidratos)
6. Sin gluten (sin trigo, centeno ni cebada)

Responde con un número o dímelo con tus propias palabras:"""),
    'dietPreferenceRequestExample': LocalizationString('Por ejemplo: 1 o "dieta regular"'),
    'allergiesRequest': LocalizationString('¿Tienes alergias alimentarias? Enuméralas separadas por comas o escribe "no":'),
    'allergiesRequestExample': LocalizationString('Por ejemplo: "nueces, lácteos" o "no"'),
    'dislikedProductsRequest': LocalizationString('¿Hay productos que no te gustan o no quieres incluir en tu dieta? Enuméralos separados por comas o escribe "no":'),
    'dislikedProductsRequestExample': LocalizationString('Por ejemplo: "champiñones, pimientos" o "no"'),
    'budgetRequest': LocalizationString('¿Cuál es tu presupuesto semanal para alimentos (en quetzales)?'),
    'budgetRequestExample': LocalizationString('Por ejemplo: 500 o "ilimitado"'),
    'completed': LocalizationString('🎉 ¡Felicidades! Has completado la configuración. Ahora puedes usar comandos como "plan", "estadísticas", "peso XX", "agua X" para interactuar con GuateFit.'),
    'invalidInput': LocalizationString('Lo siento, no pude entender tu entrada. Por favor, inténtalo de nuevo.\n\n{step_message}'),
    'weightGoalDeterminedLose': LocalizationString('Basado en tu peso actual y objetivo, veo que tu meta es perder peso. Crearé un plan de dieta acorde.'),
    'weightGoalDeterminedGain': LocalizationString('Basado en tu peso actual y objetivo, veo que tu meta es ganar peso. Crearé un plan de dieta acorde.'),
    'weightGoalDeterminedMaintain': LocalizationString('Basado en tu peso actual y objetivo, veo que tu meta es mantener tu peso. Crearé un plan de dieta acorde.'),

    'answers.yes': LocalizationString('sí'),
    'answers.no': LocalizationString('no'),
    'answers.none': LocalizationString('ninguno'),
    'answers.no_have': LocalizationString('no tengo'),

    'gender.male': LocalizationString('masculino'),
    'gender.female': LocalizationString('femenino'),
    'gender.other': LocalizationString('otro'),
    'gender.male_short': LocalizationString('masc'),
    'gender.female_short': LocalizationString('fem'),

    'activity_level.sedentary': LocalizationString('sedentario'),
    'activity_level.light': LocalizationString('ligera'),
    'activity_level.moderate': LocalizationString('moderada'),
    'activity_level.high': LocalizationString('alta'),
    'activity_level.very_high': LocalizationString('muy alta'),

    'weight_goal.lose': LocalizationString('perder'),
    'weight_goal.maintain': LocalizationString('mantener'),
    'weight_goal.gain': LocalizationString('ganar'),

    'diet_preference.regular': LocalizationString('regular'),
    'diet_preference.vegetarian': LocalizationString('vegetariana'),
    'diet_preference.vegan': LocalizationString('vegana'),
    'diet_preference.low_carb': LocalizationString('baja en carbohidratos'),
    'diet_preference.keto': LocalizationString('keto'),
    'diet_preference.gluten_free': LocalizationString('sin gluten'),

    'budget.unlimited': LocalizationString('ilimitado'),
    'budget.no_limit': LocalizationString('sin límite'),
    'budget.any': LocalizationString('cualquiera'),
}

# Create localization module
module = LocalizationModule(strings)
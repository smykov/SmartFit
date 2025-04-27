from typing import Dict, Any, List, Optional


class DietDataTransformer:
    """
    Класс для трансформации данных диетического плана из полной версии в упрощенную.
    Следует принципам Single Responsibility, предоставляя только функциональность
    преобразования данных диеты.
    """

    @staticmethod
    def transform_to_simplified(full_diet_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует полный план диеты в упрощенную версию, содержащую только
        базовую информацию о приемах пищи и их калорийности.

        Args:
            full_diet_plan: Полный план диеты в формате словаря

        Returns:
            Dict[str, Any]: Упрощенная версия плана диеты
        """
        if not full_diet_plan or 'daily_plans' not in full_diet_plan:
            return {'daily_plans': {}}

        simplified_plan = {
            'daily_plans': {}
        }

        # Обрабатываем каждый день недели
        for day, day_data in full_diet_plan.get('daily_plans', {}).items():
            simplified_day = {
                'meals': [],
                'total_calories': day_data.get('total_calories', 0)
            }

            # Обрабатываем каждый прием пищи
            for meal in day_data.get('meals', []):
                simplified_meal = {
                    'type': meal.get('type', ''),
                    'title': meal.get('title', ''),
                    'calories': meal.get('calories', 0)
                }
                simplified_day['meals'].append(simplified_meal)

            simplified_plan['daily_plans'][day] = simplified_day

        return simplified_plan

    @staticmethod
    def transform_specific_days(full_diet_plan: Dict[str, Any], days: List[str]) -> Dict[str, Any]:
        """
        Преобразует план диеты только для указанных дней.

        Args:
            full_diet_plan: Полный план диеты в формате словаря
            days: Список дней недели, которые нужно включить в упрощенный план

        Returns:
            Dict[str, Any]: Упрощенная версия плана диеты только с указанными днями
        """
        simplified_plan = DietDataTransformer.transform_to_simplified(full_diet_plan)

        # Фильтруем только нужные дни
        filtered_days = {}
        for day in days:
            if day in simplified_plan['daily_plans']:
                filtered_days[day] = simplified_plan['daily_plans'][day]

        simplified_plan['daily_plans'] = filtered_days
        return simplified_plan

    @staticmethod
    def transform_meal_types(full_diet_plan: Dict[str, Any], meal_types: List[str]) -> Dict[str, Any]:
        """
        Преобразует план диеты, включая только указанные типы приемов пищи.

        Args:
            full_diet_plan: Полный план диеты в формате словаря
            meal_types: Список типов приемов пищи, которые нужно включить

        Returns:
            Dict[str, Any]: Упрощенная версия плана с фильтрацией по типам приемов пищи
        """
        simplified_plan = {
            'daily_plans': {}
        }

        # Обрабатываем каждый день недели
        for day, day_data in full_diet_plan.get('daily_plans', {}).items():
            filtered_meals = []
            total_calories = 0

            # Фильтруем и обрабатываем каждый прием пищи
            for meal in day_data.get('meals', []):
                if meal.get('type', '') in meal_types:
                    simplified_meal = {
                        'type': meal.get('type', ''),
                        'title': meal.get('title', ''),
                        'calories': meal.get('calories', 0)
                    }
                    filtered_meals.append(simplified_meal)
                    total_calories += simplified_meal['calories']

            # Добавляем день только если есть приемы пищи после фильтрации
            if filtered_meals:
                simplified_plan['daily_plans'][day] = {
                    'meals': filtered_meals,
                    'total_calories': total_calories
                }

        return simplified_plan
# app/utils/nutrition_helper.py
from typing import Dict, Tuple


class NutritionHelper:
    """Утилиты для работы с нутриентами"""

    @staticmethod
    def calculate_macros_ratio(calories: float, proteins: float, fats: float, carbs: float) -> str:
        """
        Рассчитывает соотношение БЖУ в процентах

        Args:
            calories: Общие калории
            proteins: Белки в граммах
            fats: Жиры в граммах
            carbs: Углеводы в граммах

        Returns:
            str: Соотношение в формате "Б:XX%, Ж:XX%, У:XX%"
        """
        if calories <= 0:
            return "Б:0%, Ж:0%, У:0%"

        # Калории от каждого макронутриента
        protein_calories = proteins * 4
        fat_calories = fats * 9
        carb_calories = carbs * 4

        # Проверяем, что сумма не превышает общие калории значительно
        total_macro_calories = protein_calories + fat_calories + carb_calories
        if total_macro_calories == 0:
            return "Б:0%, Ж:0%, У:0%"

        # Используем для расчета либо указанные калории, либо сумму макронутриентов
        # (если они значительно отличаются, приоритет у макронутриентов)
        base_calories = total_macro_calories if abs(calories - total_macro_calories) > calories * 0.1 else calories

        # Рассчитываем проценты
        protein_percent = round((protein_calories / base_calories) * 100, 1)
        fat_percent = round((fat_calories / base_calories) * 100, 1)
        carb_percent = round((carb_calories / base_calories) * 100, 1)

        # Корректируем до 100% если есть небольшие расхождения
        total_percent = protein_percent + fat_percent + carb_percent
        if total_percent != 100.0 and total_percent > 0:
            correction_factor = 100.0 / total_percent
            protein_percent = round(protein_percent * correction_factor, 1)
            fat_percent = round(fat_percent * correction_factor, 1)
            carb_percent = round(100.0 - protein_percent - fat_percent, 1)

        return f"Б:{protein_percent}%, Ж:{fat_percent}%, У:{carb_percent}%"

    @staticmethod
    def calculate_macros_ratio_from_day_data(day_data: Dict) -> str:
        """
        Рассчитывает соотношение БЖУ из данных дня

        Args:
            day_data: Словарь с данными дня, содержащий total_calories, total_proteins, etc.

        Returns:
            str: Соотношение БЖУ
        """
        calories = day_data.get('total_calories', 0)
        proteins = day_data.get('total_proteins', 0)
        fats = day_data.get('total_fats', 0)
        carbs = day_data.get('total_carbs', 0)

        return NutritionHelper.calculate_macros_ratio(calories, proteins, fats, carbs)

    @staticmethod
    def validate_macros_ratio(proteins_percent: float, fats_percent: float, carbs_percent: float,
                              goal: str = 'maintain') -> Tuple[bool, str]:
        """
        Проверяет соответствие соотношения БЖУ целям пользователя

        Args:
            proteins_percent: Процент белков
            fats_percent: Процент жиров
            carbs_percent: Процент углеводов
            goal: Цель пользователя (gain, lose, maintain)

        Returns:
            Tuple[bool, str]: (соответствует_ли_норме, описание)
        """
        # Идеальные диапазоны для разных целей
        ideal_ranges = {
            'gain': {'proteins': (25, 30), 'fats': (20, 25), 'carbs': (50, 55)},
            'lose': {'proteins': (30, 35), 'fats': (20, 25), 'carbs': (40, 45)},
            'maintain': {'proteins': (20, 25), 'fats': (25, 30), 'carbs': (45, 55)}
        }

        ranges = ideal_ranges.get(goal, ideal_ranges['maintain'])

        issues = []

        # Проверяем каждый макронутриент
        if not (ranges['proteins'][0] <= proteins_percent <= ranges['proteins'][1]):
            if proteins_percent < ranges['proteins'][0]:
                issues.append(
                    f"мало белка ({proteins_percent}%, норма {ranges['proteins'][0]}-{ranges['proteins'][1]}%)")
            else:
                issues.append(
                    f"много белка ({proteins_percent}%, норма {ranges['proteins'][0]}-{ranges['proteins'][1]}%)")

        if not (ranges['fats'][0] <= fats_percent <= ranges['fats'][1]):
            if fats_percent < ranges['fats'][0]:
                issues.append(f"мало жиров ({fats_percent}%, норма {ranges['fats'][0]}-{ranges['fats'][1]}%)")
            else:
                issues.append(f"много жиров ({fats_percent}%, норма {ranges['fats'][0]}-{ranges['fats'][1]}%)")

        if not (ranges['carbs'][0] <= carbs_percent <= ranges['carbs'][1]):
            if carbs_percent < ranges['carbs'][0]:
                issues.append(f"мало углеводов ({carbs_percent}%, норма {ranges['carbs'][0]}-{ranges['carbs'][1]}%)")
            else:
                issues.append(f"много углеводов ({carbs_percent}%, норма {ranges['carbs'][0]}-{ranges['carbs'][1]}%)")

        if not issues:
            return True, "Соотношение БЖУ соответствует целям"
        else:
            return False, "; ".join(issues)
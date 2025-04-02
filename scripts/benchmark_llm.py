#!/usr/bin/env python3
"""
Скрипт для сравнения производительности различных LLM-сервисов.
Запускает набор тестовых запросов через разные сервисы и сравнивает результаты.
"""

import os
import sys
import asyncio
import time
import logging
import json
from typing import Dict, Any, List
from datetime import datetime

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.llm.llm_factory import LLMFactory
from app.services.llm.base_llm_service import BaseLLMService

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Тестовые данные
TEST_USER_DATA = {
    "gender": "male",
    "age": 30,
    "height": 175.0,
    "current_weight": 85.0,
    "target_weight": 75.0,
    "activity_level": "moderate",
    "weight_goal": "lose",
    "diet_preference": "regular",
    "budget_limit": 400.0,
    "allergies": [],
    "disliked_products": []
}

TEST_NUTRITION_QUESTIONS = [
    "Какие продукты помогают снизить вес?",
    "Сколько белка нужно в день при похудении?",
    "Какие фрукты Гватемалы самые полезные?",
    "Как правильно считать калории?",
    "Можно ли есть после 18:00?"
]


async def benchmark_diet_plan(service: BaseLLMService) -> Dict[str, Any]:
    """
    Тестирует генерацию плана диеты

    Args:
        service: LLM-сервис для тестирования

    Returns:
        Dict[str, Any]: Результаты теста
    """
    start_time = time.time()

    try:
        diet_plan = await service.generate_diet_plan(TEST_USER_DATA, days=3)
        success = diet_plan is not None and "error" not in diet_plan

        end_time = time.time()
        duration = end_time - start_time

        return {
            "success": success,
            "duration": duration,
            "plan_quality": len(json.dumps(diet_plan)) if success else 0,
        }
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        logger.error(f"Error in diet plan benchmark: {str(e)}")
        return {
            "success": False,
            "duration": duration,
            "error": str(e)
        }


async def benchmark_nutrition_questions(service: BaseLLMService) -> Dict[str, Any]:
    """
    Тестирует ответы на вопросы о питании

    Args:
        service: LLM-сервис для тестирования

    Returns:
        Dict[str, Any]: Результаты теста
    """
    results = []
    total_duration = 0
    total_success = 0

    for question in TEST_NUTRITION_QUESTIONS:
        start_time = time.time()

        try:
            answer = await service.answer_nutrition_question("test_user", question)
            success = answer is not None and len(answer) > 0

            if success:
                total_success += 1

            end_time = time.time()
            duration = end_time - start_time
            total_duration += duration

            results.append({
                "question": question,
                "success": success,
                "duration": duration,
                "answer_length": len(answer) if success else 0
            })
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            total_duration += duration

            logger.error(f"Error in nutrition question benchmark: {str(e)}")
            results.append({
                "question": question,
                "success": False,
                "duration": duration,
                "error": str(e)
            })

    return {
        "questions_count": len(TEST_NUTRITION_QUESTIONS),
        "success_count": total_success,
        "total_duration": total_duration,
        "average_duration": total_duration / len(TEST_NUTRITION_QUESTIONS),
        "details": results
    }


async def run_benchmarks():
    """
    Запускает все тесты для разных LLM-сервисов
    """
    # Список тестируемых провайдеров
    providers = ["openai", "deepseek", "hybrid"]

    results = {}

    for provider in providers:
        logger.info(f"Testing {provider} service...")

        try:
            # Создаем сервис через фабрику
            service = LLMFactory.create_llm_service(provider)

            # Запускаем тесты
            diet_results = await benchmark_diet_plan(service)
            question_results = await benchmark_nutrition_questions(service)

            # Сохраняем результаты
            results[provider] = {
                "diet_plan": diet_results,
                "nutrition_questions": question_results
            }

            logger.info(f"Completed tests for {provider}")
        except Exception as e:
            logger.error(f"Error testing {provider}: {str(e)}")
            results[provider] = {"error": str(e)}

    # Сохраняем результаты в файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"benchmark_results_{timestamp}.json"

    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Benchmark results saved to {result_file}")

    # Выводим краткую сводку
    print("\n=== BENCHMARK RESULTS ===\n")

    for provider in providers:
        if "error" in results.get(provider, {}):
            print(f"{provider.upper()}: Error - {results[provider]['error']}")
            continue

        diet_success = results[provider]["diet_plan"].get("success", False)
        diet_time = results[provider]["diet_plan"].get("duration", 0)

        questions_success = results[provider]["nutrition_questions"].get("success_count", 0)
        questions_total = results[provider]["nutrition_questions"].get("questions_count", 0)
        questions_time = results[provider]["nutrition_questions"].get("average_duration", 0)

        print(f"{provider.upper()}:")
        print(f"  Diet Plan: {'✓' if diet_success else '✗'} ({diet_time:.2f}s)")
        print(f"  Questions: {questions_success}/{questions_total} ({questions_time:.2f}s avg)")
        print()


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
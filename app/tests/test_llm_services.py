import asyncio
import unittest
from unittest.mock import patch, MagicMock

from app.services.llm.base_llm_service import BaseLLMService
from app.services.llm.deepseek_llm_service import DeepSeekLLMService
from app.services.llm.hybrid_llm_service import HybridLLMService
from app.services.llm.llm_factory import LLMFactory
from app.services.llm.openai_llm_service import OpenAILLMService


class TestLLMServices(unittest.TestCase):
    """Тесты для проверки работы LLM сервисов"""

    def test_factory_creates_openai_service(self):
        """Проверяет, что фабрика создает сервис OpenAI"""
        with patch('app.services.llm.llm_factory.OpenAILLMService') as mock_openai:
            # Настраиваем мок
            mock_instance = MagicMock(spec=OpenAILLMService)
            mock_openai.return_value = mock_instance

            # Вызываем фабрику
            service = LLMFactory.create_llm_service('openai')

            # Проверяем, что был создан экземпляр OpenAILLMService
            mock_openai.assert_called_once()
            self.assertEqual(service, mock_instance)

    def test_factory_creates_deepseek_service(self):
        """Проверяет, что фабрика создает сервис DeepSeek"""
        with patch('app.services.llm.llm_factory.DeepSeekLLMService') as mock_deepseek:
            # Настраиваем мок
            mock_instance = MagicMock(spec=DeepSeekLLMService)
            mock_deepseek.return_value = mock_instance

            # Вызываем фабрику
            service = LLMFactory.create_llm_service('deepseek')

            # Проверяем, что был создан экземпляр DeepSeekLLMService
            mock_deepseek.assert_called_once()
            self.assertEqual(service, mock_instance)

    def test_factory_creates_hybrid_service(self):
        """Проверяет, что фабрика создает гибридный сервис"""
        with patch('app.services.llm.llm_factory.HybridLLMService') as mock_hybrid:
            # Настраиваем мок
            mock_instance = MagicMock(spec=HybridLLMService)
            mock_hybrid.return_value = mock_instance

            # Вызываем фабрику
            with patch('app.services.llm.llm_factory.OpenAILLMService'), \
                    patch('app.services.llm.llm_factory.DeepSeekLLMService'):
                service = LLMFactory.create_llm_service('hybrid')

            # Проверяем, что был создан экземпляр HybridLLMService
            mock_hybrid.assert_called_once()
            self.assertEqual(service, mock_instance)

    def test_hybrid_service_task_routing(self):
        """Проверяет, что гибридный сервис правильно маршрутизирует задачи"""
        # Создаем моки для сервисов
        openai_service = MagicMock(spec=BaseLLMService)
        deepseek_service = MagicMock(spec=BaseLLMService)

        # Создаем карту задач
        services_map = {
            "default": openai_service,
            "diet_plan": openai_service,
            "nutrition_question": deepseek_service,
        }

        # Создаем гибридный сервис
        hybrid_service = HybridLLMService(services_map, "default")

        # Проверяем маршрутизацию
        self.assertEqual(hybrid_service.get_service_for_task("default"), openai_service)
        self.assertEqual(hybrid_service.get_service_for_task("diet_plan"), openai_service)
        self.assertEqual(hybrid_service.get_service_for_task("nutrition_question"), deepseek_service)
        self.assertEqual(hybrid_service.get_service_for_task("unknown_task"),
                         openai_service)  # должен использовать default

    @patch('openai.OpenAI')
    def test_openai_service_generate_completion(self, mock_openai_client):
        """Проверяет, что сервис OpenAI правильно вызывает API"""
        # Настраиваем мок
        mock_client = MagicMock()
        mock_openai_client.return_value = mock_client

        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Test response"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]

        mock_client.chat.completions.create.return_value = mock_completion

        # Создаем сервис
        service = OpenAILLMService(api_key="test_key", model="test_model")

        # Вызываем метод и проверяем результат
        result = asyncio.run(service.generate_completion("system", "user"))

        self.assertEqual(result, "Test response")
        mock_client.chat.completions.create.assert_called_once()

    @patch('requests.post')
    def test_deepseek_service_generate_completion(self, mock_post):
        """Проверяет, что сервис DeepSeek правильно вызывает API"""
        # Настраиваем мок
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        # Создаем сервис
        service = DeepSeekLLMService(api_key="test_key", model="test_model")

        # Вызываем метод и проверяем результат
        result = asyncio.run(service.generate_completion("system", "user"))

        self.assertEqual(result, "Test response")
        mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()
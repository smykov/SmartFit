# app/services/llm/model_config.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class DeepSeekModel(str, Enum):
    """Enum для моделей DeepSeek"""
    DEFAULT = "deepseek-chat"
    SMART = "deepseek-reasoner"

    @classmethod
    def get_default(cls) -> 'DeepSeekModel':
        """Возвращает модель по умолчанию"""
        return cls.DEFAULT

    @classmethod
    def get_smart(cls) -> 'DeepSeekModel':
        """Возвращает умную модель"""
        return cls.SMART

    def is_smart_model(self) -> bool:
        """Проверяет, является ли модель 'умной'"""
        return self == self.SMART

    def get_fallback_model(self) -> 'DeepSeekModel':
        """Возвращает модель для фолбека"""
        if self == self.SMART:
            return self.DEFAULT
        return self  # Если уже дефолтная модель, остаемся на ней


@dataclass
class ModelRetryConfig:
    """Конфигурация повторов для модели"""
    max_retries: int
    timeout: int
    exponential_backoff: bool = True
    base_delay: float = 1.0
    max_delay: float = 60.0

    def get_delay(self, retry_attempt: int) -> float:
        """Вычисляет задержку для попытки"""
        if not self.exponential_backoff:
            return self.base_delay

        delay = self.base_delay * (2 ** retry_attempt)
        return min(delay, self.max_delay)


@dataclass
class ModelConfig:
    """Конфигурация для конкретной модели"""
    model_name: str
    max_tokens: int
    retry_config: ModelRetryConfig
    supports_json_mode: bool = True

    @property
    def limits(self) -> Dict[str, Any]:
        """Возвращает ограничения модели"""
        return {"max_tokens": self.max_tokens}


class DeepSeekModelManager:
    """Менеджер конфигураций моделей DeepSeek"""

    def __init__(self, default_model_config: ModelConfig, smart_model_config: ModelConfig):
        """
        Инициализация менеджера моделей

        Args:
            default_model_config: Конфигурация дефолтной модели
            smart_model_config: Конфигурация умной модели
        """
        self._configs = {
            DeepSeekModel.DEFAULT: default_model_config,
            DeepSeekModel.SMART: smart_model_config
        }

    def get_config(self, model: DeepSeekModel) -> ModelConfig:
        """Получает конфигурацию для модели"""
        return self._configs[model]

    def get_retry_config(self, model: DeepSeekModel) -> ModelRetryConfig:
        """Получает конфигурацию повторов для модели"""
        return self._configs[model].retry_config

    def get_max_tokens(self, model: DeepSeekModel) -> int:
        """Получает максимальное количество токенов для модели"""
        return self._configs[model].max_tokens

    def supports_json_mode(self, model: DeepSeekModel) -> bool:
        """Проверяет, поддерживает ли модель JSON режим"""
        return self._configs[model].supports_json_mode

    @classmethod
    def from_settings(cls, settings) -> 'DeepSeekModelManager':
        """Создает менеджер из настроек приложения"""
        # Конфигурация для дефолтной модели
        default_retry_config = ModelRetryConfig(
            max_retries=getattr(settings, 'DEEPSEEK_DEFAULT_MAX_RETRIES', 2),
            timeout=getattr(settings, 'DEEPSEEK_DEFAULT_TIMEOUT', 120),
            exponential_backoff=True,
            base_delay=1.0,
            max_delay=10.0
        )

        default_config = ModelConfig(
            model_name=getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'),
            max_tokens=8192,
            retry_config=default_retry_config,
            supports_json_mode=True
        )

        # Конфигурация для умной модели
        smart_retry_config = ModelRetryConfig(
            max_retries=getattr(settings, 'DEEPSEEK_SMART_MAX_RETRIES', 3),
            timeout=getattr(settings, 'DEEPSEEK_SMART_TIMEOUT', 300),
            exponential_backoff=True,
            base_delay=2.0,
            max_delay=30.0
        )

        smart_config = ModelConfig(
            model_name=getattr(settings, 'DEEPSEEK_MODEL_SMART', 'deepseek-reasoner'),
            max_tokens=8192,
            retry_config=smart_retry_config,
            supports_json_mode=False  # reasoner не поддерживает JSON mode
        )

        return cls(default_config, smart_config)
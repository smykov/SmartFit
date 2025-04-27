# app/models/command.py
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class CommandStatus(str, Enum):
    """Статусы выполнения команды"""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    INVALID = "invalid"


class CommandSource(str, Enum):
    """Источники команды"""
    USER_TEXT = "user_text"  # Из текста пользователя
    LLM_EXTRACTION = "llm"  # Извлечено через LLM
    PATTERN_MATCH = "pattern"  # Соответствие шаблону
    FALLBACK = "fallback"  # Запасной вариант


class Command(BaseModel):
    """Модель команды для выполнения"""
    command_type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0)
    source: CommandSource = CommandSource.USER_TEXT
    confidence: float = Field(default=1.0)

    class Config:
        orm_mode = True


class CommandExtractionResult(BaseModel):
    """Результат извлечения команд из сообщения пользователя"""
    commands: List[Command] = Field(default_factory=list)
    response_message: Optional[str] = None
    fallback_to_ai: bool = Field(default=False)
    execution_required: bool = Field(default=True)
    source: CommandSource = CommandSource.LLM_EXTRACTION
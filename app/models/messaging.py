from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


class MessageType(str, Enum):
    """Типы сообщений, поддерживаемые системой"""
    TEXT = "text"
    MEDIA = "media"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    TEMPLATE = "template"


class MessageStatus(str, Enum):
    """Статусы сообщений"""
    PROCESSING = "processing"
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class MessageContext:
    """Контекст сообщения с дополнительной информацией"""
    onboarding_step: Optional[str] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
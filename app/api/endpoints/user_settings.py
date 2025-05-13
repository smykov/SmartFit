# app/api/endpoints/user_settings.py
from fastapi import APIRouter, Path, HTTPException, Depends
from typing import Dict, Any

from app.services.localization.localization_interface import ILocalizationService

router = APIRouter()


@router.put("/{user_id}/language/{language_code}")
async def set_user_language(
        user_id: str = Path(..., description="ID пользователя"),
        language_code: str = Path(..., description="Код языка (es, ru)"),
        localization_service: ILocalizationService = Depends()
):
    """
    Устанавливает предпочитаемый язык пользователя

    Args:
        user_id: ID пользователя
        language_code: Код языка (es, ru, en)

    Returns:
        Dict[str, Any]: Результат операции
    """
    # Проверяем доступные языки
    # TODO брать из модуля локализации список языков
    available_languages = ["es", "ru", "en"]

    if language_code not in available_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language code. Available options: {', '.join(available_languages)}"
        )

    # Устанавливаем язык пользователя
    success = await localization_service.set_user_language(user_id, language_code)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update user language"
        )

    return {
        "message": "User language updated successfully",
        "user_id": user_id,
        "language": language_code
    }
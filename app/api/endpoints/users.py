import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from app.db.firebase import firebase_client
from app.models.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Создает нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким телефоном
        existing_user = firebase_client.query_documents("users", "phone_number", "==", user_data.phone_number)
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this phone number already exists")
        
        # Создаем нового пользователя
        user_dict = user_data.dict()
        user_dict["is_onboarding_completed"] = True  # Если через API, то считаем онбординг завершенным
        
        # Добавляем в базу данных
        user_id = firebase_client.add_document("users", user_dict)
        
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Получаем созданного пользователя
        created_user = firebase_client.get_document("users", user_id)
        created_user["id"] = user_id
        
        return UserResponse(**created_user)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str = Path(..., description="ID пользователя")):
    """Получает пользователя по ID"""
    try:
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user["id"] = user_id
        return UserResponse(**user)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.get("/phone/{phone_number}", response_model=UserResponse)
async def get_user_by_phone(phone_number: str = Path(..., description="Номер телефона пользователя")):
    """Получает пользователя по номеру телефона"""
    try:
        users = firebase_client.query_documents("users", "phone_number", "==", phone_number)
        
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = users[0]
        return UserResponse(**user)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving user by phone: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    user_id: str = Path(..., description="ID пользователя")
):
    """Обновляет данные пользователя"""
    try:
        # Проверяем, существует ли пользователь
        existing_user = firebase_client.get_document("users", user_id)
        
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Обновляем только предоставленные поля
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        # Если есть данные для обновления
        if update_data:
            success = await firebase_client.update_document("users", user_id, update_data)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update user")
        
        # Получаем обновленного пользователя
        updated_user = firebase_client.get_document("users", user_id)
        updated_user["id"] = user_id
        
        return UserResponse(**updated_user)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(user_id: str = Path(..., description="ID пользователя")):
    """Деактивирует пользователя (soft delete)"""
    try:
        # Проверяем, существует ли пользователь
        existing_user = firebase_client.get_document("users", user_id)
        
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Для MVP просто помечаем пользователя как неактивного
        success = await firebase_client.update_document("users", user_id, {"is_active": False})
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to deactivate user")
        
        return {"message": "User successfully deactivated"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deactivating user: {str(e)}")

@router.get("/", response_model=List[UserResponse])
async def list_users(
    is_active: Optional[bool] = Query(True, description="Фильтр по активности"),
    skip: int = Query(0, description="Сколько записей пропустить"),
    limit: int = Query(100, description="Максимальное количество записей")
):
    """Получает список пользователей с возможностью фильтрации"""
    try:
        # В реальном проекте здесь была бы пагинация через Firestore
        # Для MVP получаем всех активных пользователей
        users = firebase_client.query_documents("users", "is_active", "==", is_active)
        
        # Применяем простую пагинацию в памяти
        paginated_users = users[skip:skip + limit]
        
        return [UserResponse(**user) for user in paginated_users]
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

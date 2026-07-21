from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_service
from app.schemas.user import UserCreateSchema, UserSchema, UserUpdateSchema
from app.services.exceptions import UserNotFound
from app.services.user import UserService


router = APIRouter(prefix="/users")


@router.get("")
def get_users(user_service: UserService = Depends(get_user_service)) -> list[UserSchema]:
    return user_service.list_users()

@router.post("")
def create_user(payload: UserCreateSchema,
                user_service: UserService = Depends(get_user_service)) -> UserSchema:
    return user_service.create_user(user_create=payload)

@router.patch("/{user_id}")
def update_user(payload: UserUpdateSchema,
                user_id: str,
                user_service: UserService = Depends(get_user_service)) -> UserSchema:
    try:
        return user_service.update_user(user_id=user_id,user_update=payload)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

@router.delete("/{user_id}")
def delete_user(user_id: str,
                user_service: UserService = Depends(get_user_service)) -> None:
    try:
        user_service.delete_user(user_id=user_id)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
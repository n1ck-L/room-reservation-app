from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_service, require_admin
from app.schemas.user import (
    CurrentUserSchema,
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)
from app.services.exceptions import NotFoundError
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def get_users(
    _: CurrentUserSchema = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> list[UserSchema]:
    return user_service.list_users()


@router.post("")
def create_user(
    payload: UserCreateSchema,
    _: CurrentUserSchema = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserSchema:
    try:
        return user_service.create_user(user_create=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )


@router.patch("/{user_id}")
def update_user(
    payload: UserUpdateSchema,
    user_id: str,
    _: CurrentUserSchema = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserSchema:
    try:
        return user_service.update_user(user_id=user_id, user_update=payload)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    _: CurrentUserSchema = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> None:
    try:
        user_service.delete_user(user_id=user_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_service, require_admin
from app.api.responses import ADMIN, RESP_204, RESP_404, RESP_409, combine
from app.schemas.user import (
    CurrentUserSchema,
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)
from app.services.exceptions import NotFoundError
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", responses=ADMIN)
def get_users(
    _: CurrentUserSchema = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> list[UserSchema]:
    return user_service.list_users()


@router.post(
    "", status_code=status.HTTP_201_CREATED, responses=combine(ADMIN, RESP_409)
)
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


@router.patch("/{user_id}", responses=combine(ADMIN, RESP_404))
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


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=combine(RESP_204, ADMIN, RESP_404),
)
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

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_current_user,
    get_room_service,
    require_admin,
)
from app.api.responses import (
    ADMIN,
    AUTH,
    RESP_204,
    RESP_404,
    RESP_422,
    combine,
)
from app.schemas.room import (
    RoomAvailabilitySchema,
    RoomCreateSchema,
    RoomSchema,
    RoomUpdateSchema,
)
from app.schemas.user import CurrentUserSchema
from app.services.exceptions import NotFoundError
from app.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", responses=combine(AUTH, RESP_422))
def list_rooms(
    date: date | None = Query(
        None, description="Дата для проверки свободных слотов"
    ),
    available: bool | None = Query(
        None, description="Фильтр свободных слотов"
    ),
    _: CurrentUserSchema = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
) -> list[RoomSchema] | list[RoomAvailabilitySchema]:
    if available is not None and date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Параметр available требует указания date",
        )
    return room_service.list_rooms(target_date=date, available=available)


@router.post("", status_code=status.HTTP_201_CREATED, responses=ADMIN)
def create_room(
    payload: RoomCreateSchema,
    _: CurrentUserSchema = Depends(require_admin),
    room_service: RoomService = Depends(get_room_service),
) -> RoomSchema:
    return room_service.create_room(room_create=payload)


@router.patch(
    "/{room_id}",
    responses=combine(ADMIN, RESP_404),
)
def update_room(
    payload: RoomUpdateSchema,
    room_id: str,
    _: CurrentUserSchema = Depends(require_admin),
    room_service: RoomService = Depends(get_room_service),
) -> RoomSchema:
    try:
        return room_service.update_room(room_id=room_id, room_update=payload)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=combine(RESP_204, ADMIN, RESP_404),
)
def delete_room(
    room_id: str,
    _: CurrentUserSchema = Depends(require_admin),
    room_service: RoomService = Depends(get_room_service),
) -> None:
    try:
        room_service.delete_room(room_id=room_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

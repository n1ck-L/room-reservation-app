from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_room_service
from app.schemas.room import RoomSchema, RoomCreateSchema, RoomUpdateSchema
from app.services.exceptions import NotFoundError
from app.services.room import RoomService


router = APIRouter(prefix="/rooms")


@router.get("")
def get_rooms(room_service: RoomService = Depends(get_room_service)) -> list[RoomSchema]:
    return room_service.list_rooms()

@router.post("")
def create_room(payload: RoomCreateSchema,
                room_service: RoomService = Depends(get_room_service)) -> RoomSchema:
    return room_service.create_room(room_create=payload)

@router.patch("/{room_id}")
def update_room(payload: RoomUpdateSchema,
                room_id: str,
                room_service: RoomService = Depends(get_room_service)) -> RoomSchema:
    try:
        return room_service.update_room(room_id=room_id, room_update=payload)
    except NotFoundError as e:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

@router.delete("/{room_id}")
def delete_room(room_id: str,
                room_service: RoomService = Depends(get_room_service)) -> None:
    try:
        room_service.delete_room(room_id=room_id)
    except NotFoundError as e:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
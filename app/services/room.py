from sqlalchemy.orm import Session

from app.repositories.room import RoomRepository
from app.schemas.room import RoomSchema, RoomCreateSchema, RoomUpdateSchema
from app.services.exceptions import NotFoundError


class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = RoomRepository(db)

    def list_rooms(self) -> list[RoomSchema]:
        rooms = self.repository.get_all()
        return [RoomSchema.model_validate(room) for room in rooms]

    def create_room(self, room_create: RoomCreateSchema) -> RoomSchema:
        # проверку что роль = admin
        room_orm = self.repository.create(number=room_create.number,
                                          capacity=room_create.capacity,
                                          location=room_create.location,
                                          equipment=room_create.equipment)
        self.db.commit()
        return RoomSchema.model_validate(room_orm)
    
    def update_room(self, room_id: str, room_update: RoomUpdateSchema) -> RoomSchema:
        # проверку что роль = admin
        room_for_update = self.repository.get_by_id(id=room_id)
        if room_for_update is None:
            raise NotFoundError("Комната", room_id)
        
        if room_update.number is not None:
            room_for_update.number = room_update.number
        if room_update.capacity is not None:
            room_for_update.capacity = room_update.capacity
        if room_update.location is not None:
            room_for_update.location = room_update.location
        if room_update.equipment is not None:
            room_for_update.equipment = room_update.equipment
        
        self.db.commit()
        return RoomSchema.model_validate(room_for_update)

    def delete_room(self, room_id: str) -> None:
        # проверку что роль = admin
        room_to_delete = self.repository.get_by_id(id=room_id)
        if room_to_delete is None:
            raise NotFoundError("Комната", room_id)
        
        self.repository.delete(room_to_delete)
        self.db.commit()
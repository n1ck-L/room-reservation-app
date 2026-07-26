from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.reservation import ReservationORM
from app.repositories.reservation import ReservationRepository
from app.repositories.room import RoomRepository
from app.schemas.room import (
    RoomAvailabilitySchema,
    RoomCreateSchema,
    RoomSchema,
    RoomUpdateSchema,
    TimeSlotSchema,
)
from app.services.exceptions import NotFoundError

# Рабочий день: с 9:00 до 18:00, слот = 1 час
WORK_START = time(9, 0)
WORK_END = time(18, 0)
SLOT_MINUTES = 60


class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.room_repository = RoomRepository(db)
        self.reservation_repository = ReservationRepository(db)

    def list_rooms(
        self, target_date: date | None = None, available: bool | None = None
    ) -> list[RoomSchema] | list[RoomAvailabilitySchema]:
        rooms = self.room_repository.get_all()

        # Список комнат без даты
        if target_date is None:
            return [RoomSchema.model_validate(room) for room in rooms]

        # Список комнат со свободными слотами на дату
        reservations = self.reservation_repository.get_for_date(target_date)
        result = []

        for room in rooms:
            room_reservations = [
                reservation
                for reservation in reservations
                if reservation.room_id == room.id
            ]

            free_slots = self._calc_free_slots_per_room(target_date, room_reservations)
            room_data = RoomSchema.model_validate(room)

            result.append(
                RoomAvailabilitySchema(
                    id=room_data.id,
                    number=room_data.number,
                    capacity=room_data.capacity,
                    location=room_data.location,
                    equipment=room_data.equipment,
                    date=target_date,
                    free_slots=free_slots,
                    is_bookable=len(free_slots) > 0,
                )
            )

        if available is True:
            return [room for room in result if room.is_bookable]

        if available is False:
            return [room for room in result if not room.is_bookable]

        return result

    def create_room(self, room_create: RoomCreateSchema) -> RoomSchema:
        existing = self.room_repository.get_by_number_location(
            room_create.number, room_create.location
        )
        if existing is not None:
            raise ValueError("Комната с таким номером по этому адресу уже существует")

        room_orm = self.room_repository.create(
            number=room_create.number,
            capacity=room_create.capacity,
            location=room_create.location,
            equipment=room_create.equipment,
        )
        self.db.commit()
        return RoomSchema.model_validate(room_orm)

    def update_room(self, room_id: str, room_update: RoomUpdateSchema) -> RoomSchema:
        room_for_update = self.room_repository.get_by_id(id=room_id)
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
        room_to_delete = self.room_repository.get_by_id(id=room_id)
        if room_to_delete is None:
            raise NotFoundError("Комната", room_id)

        self.room_repository.delete(room_to_delete)
        self.db.commit()

    def _calc_free_slots_per_room(
        self, target_date: date, reservations: list[ReservationORM]
    ) -> list[TimeSlotSchema]:
        slots = []
        current = datetime.combine(target_date, WORK_START)
        end_of_day = datetime.combine(target_date, WORK_END)
        step = timedelta(minutes=SLOT_MINUTES)

        while current + step <= end_of_day:
            slot_start = current
            slot_end = current + step

            is_busy = False
            for reservation in reservations:
                if (
                    reservation.start_time < slot_end
                    and reservation.end_time > slot_start
                ):
                    is_busy = True
                    break

            if not is_busy:
                slots.append(TimeSlotSchema(start=slot_start, end=slot_end))

            current = slot_end

        return slots

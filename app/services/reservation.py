from sqlalchemy.orm import Session

from app.repositories.reservation import ReservationRepository
from app.repositories.room import RoomRepository
from app.repositories.user import UserRepository
from app.schemas.reservation import (
    ReservationCreateSchema,
    ReservationSchema,
    ReservationUpdateSchema,
)
from app.schemas.user import CurrentUserSchema, UserRole
from app.services.exceptions import ForbiddenError, NotFoundError


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ReservationRepository(db)
        self.room_repository = RoomRepository(db)
        self.user_repository = UserRepository(db)

    def list_reservations(
        self, current_user: CurrentUserSchema
    ) -> list[ReservationSchema]:
        if current_user.role == UserRole.ADMIN:
            reservations = self.repository.get_all()
        else:
            reservations = self.repository.get_by_user_id(current_user.id)
        return [
            ReservationSchema.model_validate(reservation)
            for reservation in reservations
        ]

    def create_reservation(
        self,
        reservation_create: ReservationCreateSchema,
        current_user: CurrentUserSchema,
    ) -> ReservationSchema:
        room = self.room_repository.get_by_id(reservation_create.room_id)
        if room is None:
            raise NotFoundError("Комната", reservation_create.room_id)

        user_id = (
            reservation_create.user_id
            if current_user.role == UserRole.ADMIN
            else current_user.id
        )
        self._ensure_can_modify(reservation_create.user_id, current_user)

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Пользователь", user_id)

        if reservation_create.start_time >= reservation_create.end_time:
            raise ValueError("start_time должен быть раньше end_time")

        reservation_orm = self.repository.create(
            room_id=reservation_create.room_id,
            user_id=user_id,
            start_time=reservation_create.start_time,
            end_time=reservation_create.end_time,
        )
        self.db.commit()
        return ReservationSchema.model_validate(reservation_orm)

    def update_reservation(
        self,
        reservation_id: str,
        reservation_update: ReservationUpdateSchema,
        current_user: CurrentUserSchema,
    ) -> ReservationSchema:
        reservation_for_update = self.repository.get_by_id(id=reservation_id)
        if reservation_for_update is None:
            raise NotFoundError("Бронь", reservation_id)

        self._ensure_can_modify(reservation_for_update.user_id, current_user)

        if reservation_update.room_id is not None:
            room = self.room_repository.get_by_id(reservation_update.room_id)
            if room is None:
                raise NotFoundError("Комната", reservation_update.room_id)
            reservation_for_update.room_id = reservation_update.room_id

        if reservation_update.user_id is not None:
            self._ensure_can_modify(reservation_for_update.user_id, current_user)

            user = self.user_repository.get_by_id(reservation_update.user_id)
            if user is None:
                raise NotFoundError("Пользователь", reservation_update.user_id)

            reservation_for_update.user_id = reservation_update.user_id

        if reservation_update.start_time is not None:
            reservation_for_update.start_time = reservation_update.start_time
        if reservation_update.end_time is not None:
            reservation_for_update.end_time = reservation_update.end_time

        start_time = reservation_for_update.start_time
        end_time = reservation_for_update.end_time
        if start_time >= end_time:
            raise ValueError("start_time должен быть раньше end_time")

        self.db.commit()
        return ReservationSchema.model_validate(reservation_for_update)

    def delete_reservation(
        self, reservation_id: str, current_user: CurrentUserSchema
    ) -> None:
        reservation_to_delete = self.repository.get_by_id(id=reservation_id)
        if reservation_to_delete is None:
            raise NotFoundError("Бронь", reservation_id)

        self._ensure_can_modify(reservation_to_delete.user_id, current_user)

        self.repository.delete(reservation_to_delete)
        self.db.commit()

    def _ensure_can_modify(
        self, owner_id: str, current_user: CurrentUserSchema
    ) -> None:
        if current_user.role != UserRole.ADMIN and owner_id != current_user.id:
            raise ForbiddenError("Нет доступа к этой брони")

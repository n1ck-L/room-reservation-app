from datetime import date, datetime, time

from sqlalchemy import select

from app.models.reservation import ReservationORM
from app.repositories.base import BaseRepository


class ReservationRepository(BaseRepository[ReservationORM]):
    model = ReservationORM

    def get_for_date(self, target_date: date) -> list[ReservationORM]:
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        query = select(ReservationORM).where(
            ReservationORM.start_time < day_end,
            ReservationORM.end_time > day_start,
        )
        return list(self.db.scalars(query).all())

    def create(
        self,
        room_id: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> ReservationORM:
        new = ReservationORM(
            room_id=room_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add(new)
        return new

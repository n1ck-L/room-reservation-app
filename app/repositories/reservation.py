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
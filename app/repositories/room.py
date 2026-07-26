from sqlalchemy import select

from app.models.room import RoomORM
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[RoomORM]):
    model = RoomORM

    def create(
        self, number: int, capacity: int, location: str, equipment: list[str]
    ) -> RoomORM:

        new = RoomORM(
            number=number,
            capacity=capacity,
            location=location,
            equipment=equipment,
        )
        self.db.add(new)
        return new

    def get_by_number_location(self, number: int, location: str) -> RoomORM:
        query = select(RoomORM).where(
            RoomORM.number == number, RoomORM.location == location
        )
        return self.db.scalars(query).first()

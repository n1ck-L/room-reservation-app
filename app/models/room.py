from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RoomORM(Base):
    __tablename__ = "rooms"

    number: Mapped[int]
    capacity: Mapped[int]
    location: Mapped[str] = mapped_column(String(100))
    equipment: Mapped[list[str]] = mapped_column(JSON, default=list)

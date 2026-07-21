from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReservationORM(Base):
    __tablename__ = "reservations"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReservationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_id: str
    user_id: str
    start_time: datetime
    end_time: datetime


class ReservationCreateSchema(BaseModel):
    room_id: str
    user_id: str
    start_time: datetime
    end_time: datetime


class ReservationUpdateSchema(BaseModel):
    room_id: str | None = None
    user_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

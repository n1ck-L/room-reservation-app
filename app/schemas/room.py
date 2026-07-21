from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class RoomSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    number: PositiveInt
    capacity: PositiveInt
    location: str = Field(max_length=100)
    equipment: list[str] = Field(default_factory=list)


class RoomCreateSchema(BaseModel):
    number: PositiveInt
    capacity: PositiveInt
    location: str = Field(max_length=100)
    equipment: list[str] = Field(default_factory=list)


class RoomUpdateSchema(BaseModel):
    number: PositiveInt | None = None
    capacity: PositiveInt | None = None
    location: str | None = None
    equipment: list[str] | None = None


class TimeSlotSchema(BaseModel):
    start: datetime
    end: datetime


class RoomAvailabilitySchema(RoomSchema):
    """Комната + слоты на конкретную дату"""

    date: date
    free_slots: list[TimeSlotSchema]
    is_bookable: bool

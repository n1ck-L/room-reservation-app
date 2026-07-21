from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[ModelType]:
        return self.db.scalars(select(self.model)).all()

    def get_by_id(self, id: str) -> ModelType | None:
        return self.db.get(self.model, id)

    def delete(self, inst: ModelType) -> None:
        self.db.delete(inst)

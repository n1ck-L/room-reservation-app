from typing import TypeVar

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.room import RoomService
from app.services.user import UserService

ServiceType = TypeVar("ServiceType")


def service_dependency(service_class: type[ServiceType]):
    """Фабрика для инъекции зависимости сервиса"""

    def _dependency(db: Session = Depends(get_db)) -> ServiceType:
        return service_class(db)

    return _dependency


get_user_service = service_dependency(UserService)
get_room_service = service_dependency(RoomService)

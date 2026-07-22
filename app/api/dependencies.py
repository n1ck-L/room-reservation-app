from typing import TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import CurrentUserSchema, UserRole
from app.services.exceptions import NotFoundError, UnauthorizedError
from app.services.room import RoomService
from app.services.user import UserService
from app.services.reservation import ReservationService
from app.services.auth import AuthService

# Service
ServiceType = TypeVar("ServiceType")


def service_dependency(service_class: type[ServiceType]):
    """Фабрика для инъекции зависимости сервиса"""

    def _dependency(db: Session = Depends(get_db)) -> ServiceType:
        return service_class(db)

    return _dependency


get_user_service = service_dependency(UserService)
get_room_service = service_dependency(RoomService)
get_reservation_service = service_dependency(ReservationService)
get_auth_service = service_dependency(AuthService)


# Jwt
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> CurrentUserSchema:
    try:
        return auth_service.get_current_user(credentials.credentials)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


def require_admin(
    current_user: CurrentUserSchema = Depends(get_current_user),
) -> CurrentUserSchema:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для admin",
        )
    return current_user

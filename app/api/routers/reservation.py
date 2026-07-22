from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_reservation_service
from app.api.responses import (
    AUTH,
    RESP_204,
    RESP_403,
    RESP_404,
    RESP_422,
    combine,
)
from app.schemas.reservation import (
    ReservationCreateSchema,
    ReservationSchema,
    ReservationUpdateSchema,
)
from app.schemas.user import CurrentUserSchema
from app.services.exceptions import ForbiddenError, NotFoundError
from app.services.reservation import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", responses=AUTH)
def get_reservations(
    current_user: CurrentUserSchema = Depends(get_current_user),
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> list[ReservationSchema]:
    return reservation_service.list_reservations(current_user=current_user)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=combine(AUTH, RESP_403, RESP_404, RESP_422),
)
def create_reservation(
    payload: ReservationCreateSchema,
    current_user: CurrentUserSchema = Depends(get_current_user),
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationSchema:
    try:
        return reservation_service.create_reservation(
            reservation_create=payload, current_user=current_user
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.patch(
    "/{reservation_id}", responses=combine(AUTH, RESP_403, RESP_404, RESP_422)
)
def update_reservation(
    payload: ReservationUpdateSchema,
    reservation_id: str,
    current_user: CurrentUserSchema = Depends(get_current_user),
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationSchema:
    try:
        return reservation_service.update_reservation(
            reservation_id=reservation_id,
            reservation_update=payload,
            current_user=current_user,
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=combine(RESP_204, AUTH, RESP_403, RESP_404),
)
def delete_reservation(
    reservation_id: str,
    current_user: CurrentUserSchema = Depends(get_current_user),
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> None:
    try:
        reservation_service.delete_reservation(
            reservation_id=reservation_id, current_user=current_user
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

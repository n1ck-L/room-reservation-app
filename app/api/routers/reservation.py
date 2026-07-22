from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_reservation_service
from app.schemas.reservation import (
    ReservationCreateSchema,
    ReservationSchema,
    ReservationUpdateSchema,
)
from app.services.exceptions import NotFoundError
from app.services.reservation import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("")
def get_reservations(
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> list[ReservationSchema]:
    return reservation_service.list_reservations()


@router.post("")
def create_reservation(
    payload: ReservationCreateSchema,
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationSchema:
    try:
        return reservation_service.create_reservation(
            reservation_create=payload
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


@router.patch("/{reservation_id}")
def update_reservation(
    payload: ReservationUpdateSchema,
    reservation_id: str,
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationSchema:
    try:
        return reservation_service.update_reservation(
            reservation_id=reservation_id, reservation_update=payload
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


@router.delete("/{reservation_id}")
def delete_reservation(
    reservation_id: str,
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> None:
    try:
        reservation_service.delete_reservation(reservation_id=reservation_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

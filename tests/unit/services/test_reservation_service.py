from datetime import datetime, timedelta

import pytest

from app.schemas.reservation import (
    ReservationCreateSchema,
    ReservationUpdateSchema,
)
from app.schemas.user import CurrentUserSchema, UserRole
from app.services.exceptions import ForbiddenError, NotFoundError
from app.services.reservation import ReservationService


@pytest.fixture
def reservation_service(mock_db, mocker):
    mock_res_repo_cls = mocker.patch("app.services.reservation.ReservationRepository")
    mock_room_repo_cls = mocker.patch("app.services.reservation.RoomRepository")
    mock_user_repo_cls = mocker.patch("app.services.reservation.UserRepository")

    service = ReservationService(mock_db)
    service.repository = mock_res_repo_cls.return_value
    service.room_repository = mock_room_repo_cls.return_value
    service.user_repository = mock_user_repo_cls.return_value
    return service


ADMIN = CurrentUserSchema(id="admin-1", role=UserRole.ADMIN)
EMPLOYEE = CurrentUserSchema(id="emp-1", role=UserRole.EMPLOYEE)
OTHER_EMPLOYEE = CurrentUserSchema(id="emp-2", role=UserRole.EMPLOYEE)

NOW = datetime(2026, 7, 24, 10, 0)


def make_reservation_orm(
    mocker,
    res_id="res-1",
    room_id="room-1",
    user_id="emp-1",
    start_time=NOW,
    end_time=NOW + timedelta(hours=1),
):
    return mocker.MagicMock(
        id=res_id,
        room_id=room_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
    )


@pytest.mark.unit
@pytest.mark.service
@pytest.mark.reservation_service
class TestListReservations:
    def test_admin_see_all_reservations(self, reservation_service, mocker):
        reservation_service.repository.get_all.return_value = [
            make_reservation_orm(mocker)
        ]

        result = reservation_service.list_reservations(ADMIN)

        reservation_service.repository.get_all.assert_called_once()
        reservation_service.repository.get_by_user_id.assert_not_called()
        assert len(result) == 1

    def test_employee_see_only_own_reservations(self, reservation_service, mocker):
        reservation_service.repository.get_by_user_id.return_value = [
            make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        ]

        result = reservation_service.list_reservations(EMPLOYEE)

        reservation_service.repository.get_by_user_id.assert_called_once_with(
            EMPLOYEE.id
        )
        reservation_service.repository.get_all.assert_not_called()
        assert len(result) == 1
        assert result[0].user_id == EMPLOYEE.id


@pytest.mark.unit
@pytest.mark.service
@pytest.mark.reservation_service
class TestCreateReservation:
    def _payload(self, user_id="emp-1"):
        return ReservationCreateSchema(
            room_id="room-1",
            user_id=user_id,
            start_time=NOW,
            end_time=NOW + timedelta(hours=1),
        )

    def test_success_commits_and_returns_schema(
        self, reservation_service, mock_db, mocker
    ):
        reservation_service.room_repository.get_by_id.return_value = mocker.MagicMock()
        reservation_service.user_repository.get_by_id.return_value = mocker.MagicMock()
        reservation_service.repository.create.return_value = make_reservation_orm(
            mocker
        )

        result = reservation_service.create_reservation(
            self._payload(user_id=EMPLOYEE.id), EMPLOYEE
        )

        assert result.room_id == "room-1"
        assert result.user_id == EMPLOYEE.id
        mock_db.commit.assert_called_once()

    def test_unknown_room_raises_not_found(self, reservation_service):
        reservation_service.room_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match=r"Комната с id=room-1 не найден\(-a\)"):
            reservation_service.create_reservation(
                self._payload(user_id=EMPLOYEE.id), EMPLOYEE
            )

    def test_unknown_target_user_raises_not_found(self, reservation_service, mocker):
        reservation_service.room_repository.get_by_id.return_value = mocker.MagicMock()
        reservation_service.user_repository.get_by_id.return_value = None

        with pytest.raises(
            NotFoundError, match=r"Пользователь с id=emp-1 не найден\(-a\)"
        ):
            reservation_service.create_reservation(
                self._payload(user_id=EMPLOYEE.id), EMPLOYEE
            )

    def test_employee_cannot_book_for_someone_else(self, reservation_service, mocker):
        reservation_service.room_repository.get_by_id.return_value = mocker.MagicMock()

        with pytest.raises(ForbiddenError, match="Нет доступа к этой брони"):
            reservation_service.create_reservation(
                self._payload(user_id=OTHER_EMPLOYEE.id), EMPLOYEE
            )

    def test_admin_can_book_for_someone_else(
        self, reservation_service, mock_db, mocker
    ):
        reservation_service.room_repository.get_by_id.return_value = mocker.MagicMock()
        reservation_service.user_repository.get_by_id.return_value = mocker.MagicMock()
        reservation_service.repository.create.return_value = make_reservation_orm(
            mocker, user_id=EMPLOYEE.id
        )

        result = reservation_service.create_reservation(
            self._payload(user_id=EMPLOYEE.id), ADMIN
        )

        reservation_service.repository.create.assert_called_once()
        assert result.user_id == EMPLOYEE.id
        mock_db.commit.assert_called_once()

    def test_start_time_after_end_time_raises_value_error(
        self, reservation_service, mocker
    ):
        reservation_service.room_repository.get_by_id.return_value = mocker.MagicMock()
        reservation_service.user_repository.get_by_id.return_value = mocker.MagicMock()
        payload = ReservationCreateSchema(
            room_id="room-1",
            user_id=EMPLOYEE.id,
            start_time=NOW,
            end_time=NOW - timedelta(hours=1),
        )

        with pytest.raises(ValueError, match="start_time должен быть раньше end_time"):
            reservation_service.create_reservation(payload, EMPLOYEE)


@pytest.mark.unit
@pytest.mark.service
@pytest.mark.reservation_service
class TestUpdateReservation:
    def test_owner_can_update_own_reservation(
        self, reservation_service, mock_db, mocker
    ):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing
        update = ReservationUpdateSchema(
            end_time=existing.end_time + timedelta(hours=1)
        )

        result = reservation_service.update_reservation("res-1", update, EMPLOYEE)

        assert result.end_time == existing.end_time
        mock_db.commit.assert_called_once()

    def test_other_employee_cannot_update(self, reservation_service, mocker):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing
        update = ReservationUpdateSchema(
            end_time=existing.end_time + timedelta(hours=1)
        )

        with pytest.raises(ForbiddenError, match="Нет доступа к этой брони"):
            reservation_service.update_reservation("res-1", update, OTHER_EMPLOYEE)

    def test_unknown_reservation_raises_not_found(self, reservation_service):
        reservation_service.repository.get_by_id.return_value = None
        update = ReservationUpdateSchema(end_time=NOW + timedelta(hours=2))

        with pytest.raises(NotFoundError, match=r"Бронь с id=missing не найден\(-a\)"):
            reservation_service.update_reservation("missing", update, ADMIN)

    def test_room_change_validates_room_exists(self, reservation_service, mocker):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing
        reservation_service.room_repository.get_by_id.return_value = None
        update = ReservationUpdateSchema(room_id="missing")

        with pytest.raises(
            NotFoundError, match=r"Комната с id=missing не найден\(-a\)"
        ):
            reservation_service.update_reservation("res-1", update, EMPLOYEE)

    def test_user_change_validates_user_exists(self, reservation_service, mocker):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing
        reservation_service.user_repository.get_by_id.return_value = None
        update = ReservationUpdateSchema(user_id="missing")

        with pytest.raises(
            NotFoundError, match=r"Пользователь с id=missing не найден\(-a\)"
        ):
            reservation_service.update_reservation("res-1", update, EMPLOYEE)

    def test_invalid_time_range_raises_value_error(self, reservation_service, mocker):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing
        update = ReservationUpdateSchema(
            start_time=existing.end_time + timedelta(hours=1)
        )

        with pytest.raises(ValueError, match="start_time должен быть раньше end_time"):
            reservation_service.update_reservation("res-1", update, EMPLOYEE)


@pytest.mark.unit
@pytest.mark.service
@pytest.mark.reservation_service
class TestDeleteReservation:
    def test_owner_can_delete_own_reservation(
        self, reservation_service, mock_db, mocker
    ):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing

        reservation_service.delete_reservation("res-1", EMPLOYEE)

        reservation_service.repository.delete.assert_called_once_with(existing)
        mock_db.commit.assert_called_once()

    def test_admin_can_delete_any_reservation(
        self, reservation_service, mock_db, mocker
    ):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing

        reservation_service.delete_reservation("res-1", ADMIN)

        reservation_service.repository.delete.assert_called_once_with(existing)
        mock_db.commit.assert_called_once()

    def test_other_employee_cannot_delete(self, reservation_service, mocker):
        existing = make_reservation_orm(mocker, user_id=EMPLOYEE.id)
        reservation_service.repository.get_by_id.return_value = existing

        with pytest.raises(ForbiddenError, match="Нет доступа к этой брони"):
            reservation_service.delete_reservation("res-1", OTHER_EMPLOYEE)

    def test_unknown_reservation_raises_not_found(self, reservation_service):
        reservation_service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match=r"Бронь с id=missing не найден\(-a\)"):
            reservation_service.delete_reservation("missing", ADMIN)

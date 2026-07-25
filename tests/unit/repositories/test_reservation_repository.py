from datetime import date, datetime

import pytest

from app.models.reservation import ReservationORM
from app.repositories.reservation import ReservationRepository


@pytest.fixture
def repo(mock_db):
    return ReservationRepository(mock_db)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.reservation_repository
class TestCreate:
    def test_creates_reservation_with_given_fields(self, repo, mock_db):
        start = datetime(2026, 7, 25, 10, 0)
        end = datetime(2026, 7, 25, 11, 0)

        reservation = repo.create(
            room_id="room-1",
            user_id="user-1",
            start_time=start,
            end_time=end,
        )

        assert reservation is not None
        assert isinstance(reservation, ReservationORM)
        assert reservation.room_id == "room-1"
        assert reservation.user_id == "user-1"
        assert reservation.start_time == start
        assert reservation.end_time == end

    def test_repo_adds_new_reservation_to_session(self, repo, mock_db):
        reservation = repo.create(
            room_id="room-2",
            user_id="user-2",
            start_time=datetime(2026, 7, 25, 9, 0),
            end_time=datetime(2026, 7, 25, 10, 0),
        )

        mock_db.add.assert_called_once_with(reservation)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.reservation_repository
class TestGetForDate:
    def test_builds_query_and_returns_matching_reservations_as_list(
        self, repo, mock_db, mocker
    ):
        mock_select = mocker.patch("app.repositories.reservation.select")
        expected = [ReservationORM(), ReservationORM()]
        query = mock_select.return_value.where.return_value
        mock_db.scalars.return_value.all.return_value = expected

        result = repo.get_for_date(date(2026, 7, 25))

        mock_select.assert_called_once_with(ReservationORM)
        mock_select.return_value.where.assert_called_once()
        mock_db.scalars.assert_called_once_with(query)
        assert result == expected
        assert isinstance(result, list)

    def test_returns_empty_list_when_no_reservations(self, repo, mock_db, mocker):
        mocker.patch("app.repositories.reservation.select")
        mock_db.scalars.return_value.all.return_value = []

        assert repo.get_for_date(date(2026, 7, 25)) == []


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.reservation_repository
class TestGetByUserId:
    def test_builds_query_filtered_by_user_id_and_returns_list(
        self, repo, mock_db, mocker
    ):
        mock_select = mocker.patch("app.repositories.reservation.select")
        expected = [ReservationORM(), ReservationORM()]
        query = mock_select.return_value.where.return_value
        mock_db.scalars.return_value.all.return_value = expected

        result = repo.get_by_user_id("user-1")

        mock_select.assert_called_once_with(ReservationORM)
        mock_select.return_value.where.assert_called_once()
        mock_db.scalars.assert_called_once_with(query)
        assert result == expected
        assert isinstance(result, list)

    def test_returns_empty_list_when_user_has_no_reservations(
        self, repo, mock_db, mocker
    ):
        mocker.patch("app.repositories.reservation.select")
        mock_db.scalars.return_value.all.return_value = []

        assert repo.get_by_user_id("user-without-reservations") == []

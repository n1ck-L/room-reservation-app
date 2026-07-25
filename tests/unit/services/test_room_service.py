from datetime import date, datetime, time

import pytest

from app.schemas.room import RoomCreateSchema, RoomUpdateSchema
from app.services.exceptions import NotFoundError
from app.services.room import RoomService


@pytest.fixture
def room_service(mock_db, mocker):
    mock_room_repo_cls = mocker.patch("app.services.room.RoomRepository")
    mock_res_repo_cls = mocker.patch("app.services.room.ReservationRepository")

    service = RoomService(mock_db)
    service.room_repository = mock_room_repo_cls.return_value
    service.reservation_repository = mock_res_repo_cls.return_value
    return service


def make_room(
    mocker,
    room_id="room-1",
    number=101,
    capacity=4,
    location="Main",
    equipment=None,
):
    return mocker.MagicMock(
        id=room_id,
        number=number,
        capacity=capacity,
        location=location,
        equipment=equipment or [],
    )


def make_reservation(mocker, room_id, start_time, end_time):
    return mocker.MagicMock(room_id=room_id, start_time=start_time, end_time=end_time)


class TestListRooms:
    TARGET_DATE = date(2026, 7, 24)

    def test_request_without_date_returns_plain_room_schemas(
        self, room_service, mocker
    ):
        room = make_room(mocker)
        room_service.room_repository.get_all.return_value = [room]
        mocker.patch.object(room_service, "_calc_free_slots_per_room")

        result = room_service.list_rooms()

        assert len(result) == 1
        assert result[0].number == 101
        assert result[0].capacity == 4
        assert result[0].location == "Main"
        assert result[0].equipment == []
        room_service.reservation_repository.get_for_date.assert_not_called()
        room_service._calc_free_slots_per_room.assert_not_called()

    def test_no_reservations_gives_full_working_day(self, room_service, mocker):
        room = make_room(mocker)
        room_service.room_repository.get_all.return_value = [room]
        room_service.reservation_repository.get_for_date.return_value = []

        result = room_service.list_rooms(target_date=self.TARGET_DATE)

        # 9:00-18:00 по часовым слотам = 9 слотов
        assert len(result[0].free_slots) == 9
        assert result[0].is_bookable is True

    def test_time_slot_become_unavailable_after_reservation(self, room_service, mocker):
        room = make_room(mocker)
        room_service.room_repository.get_all.return_value = [room]
        reservation = make_reservation(
            mocker,
            room_id=room.id,
            start_time=datetime.combine(self.TARGET_DATE, time(10, 0)),
            end_time=datetime.combine(self.TARGET_DATE, time(11, 0)),
        )
        room_service.reservation_repository.get_for_date.return_value = [reservation]

        result = room_service.list_rooms(target_date=self.TARGET_DATE)

        free_starts = [slot.start.time() for slot in result[0].free_slots]
        assert len(free_starts) == 8
        assert time(10, 0) not in free_starts

    def test_reservations_of_other_rooms_are_ignored(self, room_service, mocker):
        room = make_room(mocker, room_id="room-1")
        room_service.room_repository.get_all.return_value = [room]
        other_room_reservation = make_reservation(
            mocker,
            room_id="room-2",
            start_time=datetime.combine(self.TARGET_DATE, time(10, 0)),
            end_time=datetime.combine(self.TARGET_DATE, time(11, 0)),
        )
        room_service.reservation_repository.get_for_date.return_value = [
            other_room_reservation
        ]

        result = room_service.list_rooms(target_date=self.TARGET_DATE)

        assert len(result[0].free_slots) == 9  # ничего не заблокировано

    def test_available_true_filters_fully_booked_rooms(self, room_service, mocker):
        free_room = make_room(mocker, room_id="room-1")
        booked_room = make_room(mocker, room_id="room-2")
        full_day_reservation = make_reservation(
            mocker,
            room_id="room-2",
            start_time=datetime.combine(self.TARGET_DATE, time(9, 0)),
            end_time=datetime.combine(self.TARGET_DATE, time(18, 0)),
        )
        room_service.room_repository.get_all.return_value = [
            free_room,
            booked_room,
        ]
        room_service.reservation_repository.get_for_date.return_value = [
            full_day_reservation
        ]

        result = room_service.list_rooms(target_date=self.TARGET_DATE, available=True)

        assert [room.id for room in result] == ["room-1"]

    def test_available_false_filters_free_rooms(self, room_service, mocker):
        free_room = make_room(mocker, room_id="room-1")
        booked_room = make_room(mocker, room_id="room-2")
        full_day_reservation = make_reservation(
            mocker,
            room_id="room-2",
            start_time=datetime.combine(self.TARGET_DATE, time(9, 0)),
            end_time=datetime.combine(self.TARGET_DATE, time(18, 0)),
        )
        room_service.room_repository.get_all.return_value = [
            free_room,
            booked_room,
        ]
        room_service.reservation_repository.get_for_date.return_value = [
            full_day_reservation
        ]

        result = room_service.list_rooms(target_date=self.TARGET_DATE, available=False)

        assert [room.id for room in result] == ["room-2"]


class TestCreateRoom:
    def test_success_commits_and_returns_schema(self, room_service, mock_db, mocker):
        room_service.room_repository.get_by_number_location.return_value = None
        room_service.room_repository.create.return_value = make_room(mocker)
        payload = RoomCreateSchema(number=101, capacity=4, location="Main")

        room_service.create_room(payload)

        room_service.room_repository.create.assert_called_once_with(
            number=payload.number,
            capacity=payload.capacity,
            location=payload.location,
            equipment=payload.equipment
        )
        mock_db.commit.assert_called_once()

    def test_duplicate_number_location_raises_value_error(self, room_service, mocker):
        room_service.room_repository.get_by_number_location.return_value = make_room(
            mocker
        )
        payload = RoomCreateSchema(number=101, capacity=4, location="Main")

        with pytest.raises(
            ValueError,
            match="Комната с таким номером по этому адресу уже существует",
        ):
            room_service.create_room(payload)


class TestUpdateRoom:
    @pytest.mark.parametrize("update_data", [
        {"number": 11, "capacity": 11},
        {"number": 1, "location": "a"},
        {"number": 10, "equipment": ["a"]},
        {"capacity": 1, "location": "b"},
        {"capacity": 10, "equipment": ["b"]},
        {"location": "c", "equipment": ["c"]},
    ])
    def test_updates_only_provided_fields(self, room_service, mock_db, mocker, update_data):
        existing = make_room(mocker)
        room_service.room_repository.get_by_id.return_value = existing
        update = RoomUpdateSchema(**update_data)

        room_service.update_room("room-1", update)

        for field, value in update_data.items():
            assert getattr(existing, field) == value
        mock_db.commit.assert_called_once()

    def test_unknown_room_raises_not_found(self, room_service):
        room_service.room_repository.get_by_id.return_value = None
        update = RoomUpdateSchema(capacity=10)

        with pytest.raises(NotFoundError, match=r"Комната с id=missing-id не найден\(-a\)"):
            room_service.update_room("missing-id", update)


class TestDeleteRoom:
    def test_success_deletes_and_commits(self, room_service, mock_db, mocker):
        existing = make_room(mocker)
        room_service.room_repository.get_by_id.return_value = existing

        room_service.delete_room("room-1")

        room_service.room_repository.delete.assert_called_once_with(existing)
        mock_db.commit.assert_called_once()

    def test_unknown_room_raises_not_found(self, room_service):
        room_service.room_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match=r"Комната с id=missing-id не найден\(-a\)"):
            room_service.delete_room("missing-id")

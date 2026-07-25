import pytest

from app.models.room import RoomORM
from app.repositories.room import RoomRepository


@pytest.fixture
def repo(mock_db):
    return RoomRepository(mock_db)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.room_repository
class TestCreate:
    def test_creates_room_with_given_fields(self, repo, mock_db):
        room = repo.create(
            number=101,
            capacity=20,
            location="Building A",
            equipment=["projector", "whiteboard"],
        )

        assert room is not None
        assert isinstance(room, RoomORM)
        assert room.number == 101
        assert room.capacity == 20
        assert room.location == "Building A"
        assert room.equipment == ["projector", "whiteboard"]

    def test_repo_adds_new_room_to_db(self, repo, mock_db):
        room = repo.create(
            number=202, capacity=10, location="Building B", equipment=[]
        )

        mock_db.add.assert_called_once_with(room)

    def test_defaults_equipment_list_is_not_shared_between_instances(self, repo, mock_db):
        room1 = repo.create(number=1, capacity=5, location="A", equipment=[])
        room1.equipment.append("mic")
        room2 = repo.create(number=2, capacity=5, location="A", equipment=[])

        assert room2.equipment == []


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.room_repository
class TestGetByNumberLocation:
    def test_builds_query_filtered_by_number_and_location(self, repo, mock_db, mocker):
        mock_select = mocker.patch("app.repositories.room.select")
        query = mock_select.return_value.where.return_value
        expected = RoomORM(number=5, capacity=8, location="X", equipment=[])
        mock_db.scalars.return_value.first.return_value = expected

        result = repo.get_by_number_location(number=5, location="X")

        mock_select.assert_called_once_with(RoomORM)
        mock_select.return_value.where.assert_called_once()
        mock_db.scalars.assert_called_once_with(query)
        mock_db.scalars.return_value.first.assert_called_once_with()
        assert result is expected

    def test_returns_none_when_no_room_matches(self, repo, mock_db, mocker):
        mocker.patch("app.repositories.room.select")
        mock_db.scalars.return_value.first.return_value = None

        result = repo.get_by_number_location(number=999, location="Nowhere")

        assert result is None

import pytest

from app.repositories.base import BaseRepository


class FakeModel:
    """Минимальная ORM модель, просто для параметризации дженерика репозитория"""


class ConcreteRepository(BaseRepository[FakeModel]):
    model = FakeModel


@pytest.fixture
def repo(mock_db):
    return ConcreteRepository(mock_db)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.room_repository
@pytest.mark.user_repository
@pytest.mark.reservation_repository
@pytest.mark.token_repository
class TestInit:
    def test_stores_db_session(self, mock_db):
        repo = ConcreteRepository(mock_db)
        assert repo.db is mock_db


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.room_repository
@pytest.mark.user_repository
@pytest.mark.reservation_repository
@pytest.mark.token_repository
class TestGetAll:
    def test_builds_select_for_model_and_returns_all_scalars(
        self, repo, mock_db, mocker
    ):
        mock_select = mocker.patch("app.repositories.base.select")
        expected = [FakeModel(), FakeModel()]
        mock_db.scalars.return_value.all.return_value = expected

        result = repo.get_all()

        mock_select.assert_called_once_with(FakeModel)
        mock_db.scalars.assert_called_once_with(mock_select.return_value)
        mock_db.scalars.return_value.all.assert_called_once_with()
        assert result == expected

    def test_returns_empty_list_when_no_rows(self, repo, mock_db, mocker):
        mocker.patch("app.repositories.base.select")
        mock_db.scalars.return_value.all.return_value = []

        assert repo.get_all() == []


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.room_repository
@pytest.mark.user_repository
@pytest.mark.reservation_repository
@pytest.mark.token_repository
class TestGetById:
    def test_delegates_to_session_get(self, repo, mock_db):
        expected = FakeModel()
        mock_db.get.return_value = expected

        result = repo.get_by_id("some-id")

        mock_db.get.assert_called_once_with(FakeModel, "some-id")
        assert result is expected

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.get.return_value = None

        assert repo.get_by_id("missing-id") is None


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.room_repository
@pytest.mark.user_repository
@pytest.mark.reservation_repository
@pytest.mark.token_repository
class TestDelete:
    def test_calls_session_delete_with_instance(self, repo, mock_db):
        inst = FakeModel()

        result = repo.delete(inst)

        mock_db.delete.assert_called_once_with(inst)
        assert result is None

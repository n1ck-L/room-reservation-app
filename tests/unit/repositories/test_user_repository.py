import pytest

from app.models.user import UserORM
from app.repositories.user import UserRepository
from app.schemas.user import UserRole


@pytest.fixture
def repo(mock_db):
    return UserRepository(mock_db)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.user_repository
class TestCreate:
    def test_creates_user_with_given_fields(self, repo, mock_db):
        user = repo.create(email="test@test.ru", login="test", password="test")

        assert user is not None
        assert isinstance(user, UserORM)
        assert user.login == "test"
        assert user.email == "test@test.ru"
        assert user.password == "test"
        assert user.role == UserRole.EMPLOYEE

    def test_repo_adds_new_user_to_db(self, repo, mock_db):
        user = repo.create(email="test@test.ru", login="test", password="test")

        mock_db.add.assert_called_once_with(user)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.user_repository
class TestGetByLogin:
    def test_builds_query_filtered_by_login(self, repo, mock_db, mocker):
        mock_select = mocker.patch("app.repositories.user.select")
        query = mock_select.return_value.where.return_value
        expected = UserORM(email="test@test.ru", login="test", password="test")
        mock_db.scalars.return_value.first.return_value = expected

        result = repo.get_by_login(login="test")

        mock_select.assert_called_once_with(UserORM)
        mock_select.return_value.where.assert_called_once()
        mock_db.scalars.assert_called_once_with(query)
        mock_db.scalars.return_value.first.assert_called_once_with()
        assert result is expected

    def test_returns_none_when_no_user_matches(self, repo, mock_db, mocker):
        mocker.patch("app.repositories.user.select")
        mock_db.scalars.return_value.first.return_value = None

        result = repo.get_by_login(login="test")

        assert result is None

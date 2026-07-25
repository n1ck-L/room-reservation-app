import pytest

from app.schemas.user import UserCreateSchema, UserRole, UserUpdateSchema
from app.services.exceptions import NotFoundError
from app.services.user import UserService


@pytest.fixture
def user_service(mock_db, mocker):
    mock_repo_cls = mocker.patch("app.services.user.UserRepository")
    service = UserService(mock_db)
    service.repository = mock_repo_cls.return_value
    return service


def make_user_orm(
    mocker,
    user_id="user-1",
    email="ivan@example.com",
    login="ivan",
    password="hashed",
    role=UserRole.EMPLOYEE,
):
    return mocker.MagicMock(
        id=user_id, email=email, login=login, password=password, role=role
    )


class TestListUsers:
    def test_empty_repository_returns_empty_list(self, user_service):
        user_service.repository.get_all.return_value = []

        assert user_service.list_users() == []

    def test_returns_mapped_schemas(self, user_service, mocker):
        user_service.repository.get_all.return_value = [make_user_orm(mocker)]

        result = user_service.list_users()

        assert len(result) == 1
        assert result[0].id == "user-1"
        assert result[0].login == "ivan"
        assert result[0].email == "ivan@example.com"
        assert result[0].password.get_secret_value() == "hashed"
        assert result[0].role == "employee"


class TestCreateUser:
    def test_success_hashes_password_and_commits(self, user_service, mock_db, mocker):
        user_service.repository.get_by_login.return_value = None
        user_service.repository.create.return_value = make_user_orm(mocker)
        mock_hash = mocker.patch(
            "app.services.user.hash_password", return_value="hashed"
        )
        payload = UserCreateSchema(
            email="ivan@example.com", login="ivan", password="secret123"
        )

        result = user_service.create_user(payload)

        mock_hash.assert_called_once_with("secret123")
        user_service.repository.create.assert_called_once_with(
            email="ivan@example.com",
            login="ivan",
            password="hashed",
            role=UserRole.EMPLOYEE,
        )
        mock_db.commit.assert_called_once()
        assert result.login == "ivan"
        assert result.email == "ivan@example.com"
        assert result.password.get_secret_value() == "hashed"
        assert result.role == "employee"

    def test_duplicate_login_raises_value_error(self, user_service, mocker):
        user_service.repository.get_by_login.return_value = make_user_orm(mocker)
        payload = UserCreateSchema(
            email="ivan@example.com", login="ivan", password="secret123"
        )

        with pytest.raises(
            ValueError, match="Пользователь с таким login уже существует"
        ):
            user_service.create_user(payload)


class TestUpdateUser:
    @pytest.mark.parametrize(
        "update_data",
        [
            {"email": "a@example.com", "login": "a"},
            {"email": "b@example.com", "password": "a"},
            {"email": "c@example.com", "role": "employee"},
            {"role": "admin", "password": "b"},
            {"role": "employee", "login": "b"},
            {"login": "c", "password": "c"},
        ],
    )
    def test_updates_only_provided_fields(
        self, user_service, mock_db, mocker, update_data
    ):
        existing = make_user_orm(mocker)
        user_service.repository.get_by_id.return_value = existing
        update = UserUpdateSchema(**update_data)

        user_service.update_user("user-1", update)

        for field, value in update_data.items():
            if field == "password":
                assert existing.password != value
            else:
                assert getattr(existing, field) == value
        mock_db.commit.assert_called_once()

    def test_unknown_user_raises_not_found(self, user_service):
        user_service.repository.get_by_id.return_value = None
        update = UserUpdateSchema(email="new@example.com")

        with pytest.raises(
            NotFoundError,
            match=r"Пользователь с id=missing-id не найден\(-a\)",
        ):
            user_service.update_user("missing-id", update)


class TestDeleteUser:
    def test_success_deletes_and_commits(self, user_service, mock_db, mocker):
        existing = make_user_orm(mocker)
        user_service.repository.get_by_id.return_value = existing

        user_service.delete_user("user-1")

        user_service.repository.delete.assert_called_once_with(existing)
        mock_db.commit.assert_called_once()

    def test_unknown_user_raises_not_found(self, user_service):
        user_service.repository.get_by_id.return_value = None

        with pytest.raises(
            NotFoundError,
            match=r"Пользователь с id=missing-id не найден\(-a\)",
        ):
            user_service.delete_user("missing-id")


class TestEnsureDefaultAdmin:
    def _settings(self, mocker, seed=True):
        settings = mocker.MagicMock()
        settings.SEED_DEFAULT_ADMIN = seed
        settings.DEFAULT_ADMIN_LOGIN = "admin"
        settings.DEFAULT_ADMIN_EMAIL = "admin@example.com"
        settings.DEFAULT_ADMIN_PASSWORD = mocker.MagicMock(
            get_secret_value=lambda: "admin-pass"
        )
        return settings

    def test_seeding_disabled_does_nothing(self, user_service, mock_db, mocker):
        mocker.patch("app.services.user.settings", self._settings(mocker, seed=False))

        user_service.ensure_default_admin()

        user_service.repository.get_by_login.assert_not_called()
        user_service.repository.create.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_admin_already_exists_does_nothing(self, user_service, mock_db, mocker):
        mocker.patch("app.services.user.settings", self._settings(mocker, seed=True))
        user_service.repository.get_by_login.return_value = make_user_orm(
            mocker, login="admin"
        )

        user_service.ensure_default_admin()

        user_service.repository.create.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_creates_admin_when_missing(self, user_service, mock_db, mocker):
        mocker.patch("app.services.user.settings", self._settings(mocker, seed=True))
        user_service.repository.get_by_login.return_value = None
        mocker.patch("app.services.user.hash_password", return_value="hashed-admin")

        user_service.ensure_default_admin()

        user_service.repository.create.assert_called_once_with(
            email="admin@example.com",
            login="admin",
            password="hashed-admin",
            role=UserRole.ADMIN,
        )
        mock_db.commit.assert_called_once()

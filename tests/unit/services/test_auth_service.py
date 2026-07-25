from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.schemas.auth import LoginSchema, TokenRefreshSchema, TokenRevokeSchema
from app.services.auth import AuthService
from app.services.exceptions import NotFoundError, UnauthorizedError


@pytest.fixture
def auth_service(mock_db, mocker):
    mock_refresh_repo_cls = mocker.patch("app.services.auth.RefreshTokenRepository")
    mock_user_repo_cls = mocker.patch("app.services.auth.UserRepository")

    service = AuthService(mock_db)
    service.refresh_repository = mock_refresh_repo_cls.return_value
    service.user_repository = mock_user_repo_cls.return_value
    return service


def make_user(mocker, user_id="user-1", password="hashed-pass"):
    return mocker.MagicMock(id=user_id, password=password)


def make_refresh_orm(mocker, is_revoked=False, expires_delta=timedelta(days=1)):
    return mocker.MagicMock(
        is_revoked=is_revoked,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta,
    )


class TestLogin:
    def test_success_returns_token_pair_and_persists_refresh(
        self, auth_service, mock_db, mocker
    ):
        auth_service.user_repository.get_by_login.return_value = make_user(mocker)
        payload = LoginSchema(login="ivan", password="secret123")

        mocker.patch("app.services.auth.verify_password", return_value=True)
        mocker.patch("app.services.auth.create_access_token", return_value="access-tok")
        mocker.patch(
            "app.services.auth.create_refresh_token",
            return_value="refresh-tok",
        )

        result = auth_service.login(payload)

        assert result.access_token == "access-tok"
        assert result.refresh_token == "refresh-tok"
        auth_service.refresh_repository.create.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_unknown_login_raises_unauthorized(self, auth_service):
        auth_service.user_repository.get_by_login.return_value = None
        payload = LoginSchema(login="ivan", password="secret123")

        with pytest.raises(UnauthorizedError, match="Неверный login или password"):
            auth_service.login(payload)

    def test_wrong_password_raises_unauthorized(self, auth_service, mocker):
        auth_service.user_repository.get_by_login.return_value = make_user(mocker)
        mocker.patch("app.services.auth.verify_password", return_value=False)
        payload = LoginSchema(login="ivan", password="wrong-pass")

        with pytest.raises(UnauthorizedError, match="Неверный login или password"):
            auth_service.login(payload)


class TestRefreshToken:
    def test_success_returns_new_access_token(self, auth_service, mocker):
        auth_service.refresh_repository.get_by_token.return_value = make_refresh_orm(
            mocker
        )
        mocker.patch(
            "app.services.auth.decode_refresh_token",
            return_value={"type": "refresh", "sub": "user-1"},
        )
        mocker.patch("app.services.auth.create_access_token", return_value="new-access")
        token_data = TokenRefreshSchema(refresh_token="valid-refresh")

        result = auth_service.refresh_token(token_data)

        assert result.access_token == "new-access"
        assert result.refresh_token == "valid-refresh"

    def test_invalid_jwt_raises_unauthorized(self, auth_service, mocker):
        mocker.patch("app.services.auth.decode_refresh_token", side_effect=JWTError)
        token_data = TokenRefreshSchema(refresh_token="garbage")

        with pytest.raises(UnauthorizedError, match="Невалидный refresh-токен"):
            auth_service.refresh_token(token_data)

    def test_wrong_token_type_raises_unauthorized(self, auth_service, mocker):
        mocker.patch(
            "app.services.auth.decode_refresh_token",
            return_value={"type": "access", "sub": "user-1"},
        )
        token_data = TokenRefreshSchema(refresh_token="access-token")

        with pytest.raises(UnauthorizedError, match="Неверный тип токена"):
            auth_service.refresh_token(token_data)

    def test_unknown_token_raises_unauthorized(self, auth_service, mocker):
        auth_service.refresh_repository.get_by_token.return_value = None
        mocker.patch(
            "app.services.auth.decode_refresh_token",
            return_value={"type": "refresh", "sub": "user-1"},
        )
        token_data = TokenRefreshSchema(refresh_token="unknown")

        with pytest.raises(UnauthorizedError, match="Refresh-токен недействителен"):
            auth_service.refresh_token(token_data)

    def test_revoked_token_raises_unauthorized(self, auth_service, mocker):
        auth_service.refresh_repository.get_by_token.return_value = make_refresh_orm(
            mocker, is_revoked=True
        )
        mocker.patch(
            "app.services.auth.decode_refresh_token",
            return_value={"type": "refresh", "sub": "user-1"},
        )
        token_data = TokenRefreshSchema(refresh_token="refresh_token")

        with pytest.raises(UnauthorizedError, match="Refresh-токен недействителен"):
            auth_service.refresh_token(token_data)

    def test_expired_token_raises_unauthorized(self, auth_service, mocker):
        auth_service.refresh_repository.get_by_token.return_value = make_refresh_orm(
            mocker, expires_delta=timedelta(days=-1)
        )
        mocker.patch(
            "app.services.auth.decode_refresh_token",
            return_value={"type": "refresh", "sub": "user-1"},
        )
        token_data = TokenRefreshSchema(refresh_token="expired")

        with pytest.raises(UnauthorizedError, match="Refresh-токен истёк"):
            auth_service.refresh_token(token_data)


class TestRevokeToken:
    def test_existing_token_gets_revoked_and_committed(
        self, auth_service, mock_db, mocker
    ):
        refresh_orm = make_refresh_orm(mocker)
        auth_service.refresh_repository.get_by_token.return_value = refresh_orm
        token_data = TokenRevokeSchema(refresh_token="some-token")

        auth_service.revoke_token(token_data)

        assert refresh_orm.is_revoked is True
        mock_db.commit.assert_called_once()

    def test_unknown_token_nop(self, auth_service, mock_db):
        auth_service.refresh_repository.get_by_token.return_value = None
        token_data = TokenRevokeSchema(refresh_token="unknown")

        auth_service.revoke_token(token_data)

        mock_db.commit.assert_not_called()


class TestGetCurrentUser:
    def test_success_returns_current_user(self, auth_service, mocker):
        auth_service.user_repository.get_by_id.return_value = mocker.MagicMock(
            id="user-1", role="admin"
        )
        mocker.patch(
            "app.services.auth.decode_access_token",
            return_value={"type": "access", "sub": "user-1"},
        )

        result = auth_service.get_current_user("some-token")

        assert result.id == "user-1"

    def test_invalid_jwt_raises_unauthorized(self, auth_service, mocker):
        mocker.patch("app.services.auth.decode_access_token", side_effect=JWTError)

        with pytest.raises(UnauthorizedError, match="Невалидный токен"):
            auth_service.get_current_user("garbage")

    def test_wrong_token_type_raises_unauthorized(self, auth_service, mocker):
        mocker.patch(
            "app.services.auth.decode_access_token",
            return_value={"type": "refresh", "sub": "user-1"},
        )

        with pytest.raises(UnauthorizedError, match="Неверный тип токена"):
            auth_service.get_current_user("refresh-token")

    def test_missing_sub_raises_unauthorized(self, auth_service, mocker):
        mocker.patch(
            "app.services.auth.decode_access_token",
            return_value={"type": "access"},
        )

        with pytest.raises(UnauthorizedError, match="Невалидный токен"):
            auth_service.get_current_user("token-without-sub")

    def test_unknown_user_raises_not_found(self, auth_service, mocker):
        auth_service.user_repository.get_by_id.return_value = None
        mocker.patch(
            "app.services.auth.decode_access_token",
            return_value={"type": "access", "sub": "missing"},
        )

        with pytest.raises(
            NotFoundError, match=r"Пользователь с id=missing не найден\(-a\)"
        ):
            auth_service.get_current_user("token")

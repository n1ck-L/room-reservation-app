import pytest
 
from app.services.exceptions import NotFoundError, UnauthorizedError
 
 
@pytest.fixture
def login_payload():
    return {"login": "alice", "password": "secret"}
 
 
@pytest.fixture
def refresh_payload():
    return {"refresh_token": "some-refresh-token"}
 
 
@pytest.fixture
def revoke_payload():
    return {"refresh_token": "some-refresh-token"}
 
 
@pytest.fixture
def room_create_payload():
    return {
        "number": 1,
        "capacity": 1,
        "location": "a",
        "equipment": ["a", "b"],
    }
 
 
class TestLoginResponse:
    """POST /auth/tokens"""
 
    def test_login_returns_200_and_tokens(
        self, anonymous_client, mock_auth_service, login_payload
    ):
        response = anonymous_client.post("/auth/tokens", json=login_payload)
 
        assert response.status_code == 200
        mock_auth_service.login.assert_called_once()
        
    def test_login_returns_401_for_invalid_credentials(
        self, anonymous_client, mock_auth_service, login_payload
    ):
        mock_auth_service.login.side_effect = UnauthorizedError(
            "Неверный login или password"
        )
 
        response = anonymous_client.post("/auth/tokens", json=login_payload)
 
        assert response.status_code == 401
        assert response.json()["detail"] == "Неверный login или password"
 
    @pytest.mark.parametrize(
        "payload",
        [
            {"login": "alice"},
            {"password": "secret"},
            {},
        ],
    )
    def test_login_returns_422_for_missing_fields(
        self, anonymous_client, mock_auth_service, payload
    ):
        response = anonymous_client.post("/auth/tokens", json=payload)
 
        assert response.status_code == 422
        mock_auth_service.login.assert_not_called()


class TestResfreshResponse:
    """POST /auth/tokens/refresh"""

    def test_refresh_returns_200_and_tokens(
            self, anonymous_client, mock_auth_service, refresh_payload
        ):
            response = anonymous_client.post("/auth/tokens/refresh", json=refresh_payload)
     
            assert response.status_code == 200
            mock_auth_service.refresh_token.assert_called_once()

    def test_refresh_returns_401_for_invalid_credentials(
            self, anonymous_client, mock_auth_service, refresh_payload
        ):
        mock_auth_service.refresh_token.side_effect = UnauthorizedError(
            "Невалидный refresh-токен"
        )
    
        response = anonymous_client.post("/auth/tokens/refresh", json=refresh_payload)
    
        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный refresh-токен"
     
    def test_refresh_returns_422_for_missing_field(
        self, anonymous_client, mock_auth_service
    ):
        response = anonymous_client.post("/auth/tokens/refresh", json={})
 
        assert response.status_code == 422
        mock_auth_service.refresh_token.assert_not_called()


class TestRevokeResponse:
    """POST /auth/tokens/revoke"""
 
    def test_revoke_returns_204(self, anonymous_client, mock_auth_service, revoke_payload):
        response = anonymous_client.post("/auth/tokens/revoke", json=revoke_payload)
 
        assert response.status_code == 204
        assert response.content == b""
        mock_auth_service.revoke_token.assert_called_once()
 
    def test_revoke_returns_422_for_missing_field(self, anonymous_client, mock_auth_service):
        response = anonymous_client.post("/auth/tokens/revoke", json={})
 
        assert response.status_code == 422
        mock_auth_service.revoke_token.assert_not_called()


class TestGetCurrentUserDependency:
 
    def test_valid_token_grants_access(
        self, anonymous_client, mock_auth_service, employee_user
    ):
        mock_auth_service.get_current_user.return_value = employee_user
 
        response = anonymous_client.get(
            "/rooms", headers={"Authorization": "Bearer valid-token"}
        )
 
        assert response.status_code == 200
        mock_auth_service.get_current_user.assert_called_once_with("valid-token")
 
    def test_missing_token_returns_401(self, anonymous_client, mock_auth_service):
        response = anonymous_client.get("/rooms")
 
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_auth_service.get_current_user.assert_not_called()
 
    def test_invalid_token_returns_401(
        self, anonymous_client, mock_auth_service
    ):
        mock_auth_service.get_current_user.side_effect = UnauthorizedError(
            "Невалидный токен"
        )
 
        response = anonymous_client.get(
            "/rooms", headers={"Authorization": "Bearer bad-token"}
        )
 
        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        assert response.headers.get("www-authenticate") == "Bearer"
 
    def test_token_for_deleted_user_returns_401(
        self, anonymous_client, mock_auth_service
    ):
        mock_auth_service.get_current_user.side_effect = NotFoundError(
            "Пользователь", "missing-id"
        )
 
        response = anonymous_client.get(
            "/rooms", headers={"Authorization": "Bearer stale-token"}
        )
 
        assert response.status_code == 401
import pytest

from app.services.exceptions import NotFoundError
from tests.unit.routers.conftest import AUTH_DENIAL_CASES_ADMIN


@pytest.fixture
def create_payload():
    return {
        "email": "updated@example.com",
        "login": "updated",
        "password": "secret",
    }


@pytest.fixture
def update_payload():
    return {"email": "updated@example.com"}


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.user_router
class TestUsersGetResponse:
    """GET /users"""

    def test_get_users_returns_list(self, admin_client, mock_user_service):
        response = admin_client.get("/users")

        assert response.status_code == 200
        mock_user_service.list_users.assert_called_once()

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_get_users_denies_unauthorized(
        self, request, client_fixture, expected_status, mock_user_service
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.get("/users")

        assert response.status_code == expected_status
        mock_user_service.list_users.assert_not_called()

    def test_get_users_returns_401_without_auth(
        self, anonymous_client, mock_user_service
    ):
        response = anonymous_client.get("/users")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_user_service.list_users.assert_not_called()

    def test_get_users_returns_401_with_invalid_token(
        self, invalid_token_client, mock_user_service
    ):
        response = invalid_token_client.get(
            "/users",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_user_service.list_users.assert_not_called()

    def test_get_users_returns_422_for_validation_error(
        self, validation_error_client, mock_user_service
    ):
        response = validation_error_client.get("/users")

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["loc"] == ["query", "_"]
        assert detail[0]["type"] == "missing"
        mock_user_service.list_users.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.user_router
class TestUserCreateResponse:
    """POST /users"""

    def test_create_user_returns_201_and_created_user(
        self, admin_client, mock_user_service, create_payload
    ):
        response = admin_client.post("/users", json=create_payload)

        assert response.status_code == 201
        mock_user_service.create_user.assert_called_once()

    def test_create_user_returns_409_when_login_taken(
        self, admin_client, mock_user_service, create_payload
    ):
        mock_user_service.create_user.side_effect = ValueError(
            "Пользователь с таким login уже существует"
        )

        response = admin_client.post("/users", json=create_payload)

        assert response.status_code == 409
        assert response.json()["detail"] == "Пользователь с таким login уже существует"

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_create_user_denies_unauthorized(
        self,
        request,
        client_fixture,
        expected_status,
        mock_user_service,
        create_payload,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.post("/users", json=create_payload)

        assert response.status_code == expected_status
        mock_user_service.create_user.assert_not_called()

    def test_create_user_returns_401_without_auth(
        self, anonymous_client, mock_user_service, create_payload
    ):
        response = anonymous_client.post("/users", json=create_payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_user_service.list_users.assert_not_called()

    def test_create_user_returns_401_with_invalid_token(
        self, invalid_token_client, mock_user_service, create_payload
    ):
        response = invalid_token_client.post(
            "/users",
            json=create_payload,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_user_service.create_user.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.user_router
class TestUserUpdateResponse:
    """PATCH /users/{user_id}"""

    def test_update_user_returns_200_and_updated_user(
        self, admin_client, mock_user_service, update_payload
    ):
        response = admin_client.patch("/users/u1", json=update_payload)

        assert response.status_code == 200
        mock_user_service.update_user.assert_called_once()

    def test_update_user_returns_404_when_not_found(
        self, admin_client, mock_user_service, update_payload
    ):
        mock_user_service.update_user.side_effect = NotFoundError(
            "Пользователь", "missing"
        )

        response = admin_client.patch("/users/missing", json=update_payload)

        assert response.status_code == 404

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_update_user_denies_unauthorized(
        self,
        request,
        client_fixture,
        expected_status,
        mock_user_service,
        update_payload,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.patch("/users/u1", json=update_payload)

        assert response.status_code == expected_status
        mock_user_service.update_user.assert_not_called()

    def test_update_user_returns_401_without_auth(
        self, anonymous_client, mock_user_service, update_payload
    ):
        response = anonymous_client.patch("/users/u1", json=update_payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_user_service.list_users.assert_not_called()

    def test_update_user_returns_401_with_invalid_token(
        self, invalid_token_client, mock_user_service, update_payload
    ):
        response = invalid_token_client.patch(
            "/users/u1",
            json=update_payload,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_user_service.create_user.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.user_router
class TestUserDeleteResponse:
    """DELETE /users/{user_id}"""

    def test_delete_user_returns_204(self, admin_client, mock_user_service):
        response = admin_client.delete("/users/u1")

        assert response.status_code == 204
        assert response.content == b""
        mock_user_service.delete_user.assert_called_once_with(user_id="u1")

    def test_delete_user_returns_404_when_not_found(
        self, admin_client, mock_user_service
    ):
        mock_user_service.delete_user.side_effect = NotFoundError(
            "Пользователь", "missing"
        )

        response = admin_client.delete("/users/missing")

        assert response.status_code == 404

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_delete_user_denies_unauthorized(
        self, request, client_fixture, expected_status, mock_user_service
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.delete("/users/u1")

        assert response.status_code == expected_status
        mock_user_service.delete_user.assert_not_called()

    def test_delete_user_returns_401_without_auth(
        self, anonymous_client, mock_user_service
    ):
        response = anonymous_client.delete("/users/u1")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_user_service.list_users.assert_not_called()

    def test_delete_user_returns_401_with_invalid_token(
        self, invalid_token_client, mock_user_service
    ):
        response = invalid_token_client.delete(
            "/users/u1",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_user_service.create_user.assert_not_called()

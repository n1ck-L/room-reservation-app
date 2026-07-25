import datetime

import pytest

from app.services.exceptions import NotFoundError
from tests.unit.routers.conftest import (
    AUTH_DENIAL_CASES_ADMIN,
    AUTH_DENIAL_CASES_NO_ADMIN,
)


@pytest.fixture
def create_payload():
    return {
        "number": 1,
        "capacity": 1,
        "location": "a",
        "equipment": ["a", "b"],
    }


@pytest.fixture
def update_payload():
    return {"equipment": ["a", "b", "c"]}


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.room_router
class TestRoomsGetResponse:
    """GET /rooms"""

    def test_get_rooms_returns_list(self, admin_client, mock_room_service):
        response = admin_client.get("/rooms")

        assert response.status_code == 200
        mock_room_service.list_rooms.assert_called_once()

    @pytest.mark.parametrize(
        "query_params",
        [
            {"date": "2026-07-23", "available": "true"},
            {"date": "2026-07-23", "available": "false"},
        ],
    )
    def test_get_rooms_returns_list_with_query_params(
        self, admin_client, mock_room_service, query_params
    ):
        response = admin_client.get("/rooms", params=query_params)

        assert response.status_code == 200
        mock_room_service.list_rooms.assert_called_once_with(
            target_date=datetime.date(2026, 7, 23),
            available=True if query_params["available"] == "true" else False,
        )

    def test_get_rooms_with_date_without_available_returns_list(
        self, admin_client, mock_room_service
    ):
        response = admin_client.get("/rooms", params={"date": "2026-07-23"})

        assert response.status_code == 200
        mock_room_service.list_rooms.assert_called_once_with(
            target_date=datetime.date(2026, 7, 23), available=None
        )

    def test_get_rooms_with_available_without_date_returns_422(
        self, admin_client, mock_room_service
    ):
        response = admin_client.get("/rooms", params={"available": "true"})

        assert response.status_code == 422
        assert response.json()["detail"] == "Параметр available требует указания date"
        mock_room_service.list_rooms.assert_not_called()

    @pytest.mark.parametrize(
        "params",
        [
            {"date": "abc"},
            {"date": "123"},
            {"date": 123},
            {"date": "2026-07-23", "available": "abc"},
            {"date": "2026-07-23", "available": "123"},
            {"date": "2026-07-23", "available": 123},
        ],
    )
    def test_get_rooms_invalid_params_returns_422(
        self, admin_client, mock_room_service, params
    ):
        response = admin_client.get("/rooms", params=params)

        assert response.status_code == 422
        mock_room_service.list_rooms.assert_not_called()

    @pytest.mark.parametrize(
        "client_fixture, expected_status", AUTH_DENIAL_CASES_NO_ADMIN
    )
    def test_get_rooms_denies_unauthorized(
        self, request, client_fixture, expected_status, mock_room_service
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.get("/rooms")

        assert response.status_code == expected_status
        mock_room_service.list_rooms.assert_not_called()

    def test_get_rooms_returns_401_without_auth(
        self, anonymous_client, mock_user_service
    ):
        response = anonymous_client.get("/users")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_user_service.list_users.assert_not_called()

    def test_get_rooms_returns_401_with_invalid_token(
        self, invalid_token_client, mock_room_service
    ):
        response = invalid_token_client.get(
            "/rooms",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_room_service.list_rooms.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.room_router
class TestRoomCreateResponse:
    """POST /rooms"""

    def test_create_room_returns_201_and_created_room(
        self, admin_client, mock_room_service, create_payload
    ):
        response = admin_client.post("/rooms", json=create_payload)

        assert response.status_code == 201
        mock_room_service.create_room.assert_called_once()

    def test_create_room_returns_409_when_number_taken(
        self, admin_client, mock_room_service, create_payload
    ):
        mock_room_service.create_room.side_effect = ValueError(
            "Комната с таким номером по этому адресу уже существует"
        )

        response = admin_client.post("/rooms", json=create_payload)

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Комната с таким номером по этому адресу уже существует"
        )

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_create_room_denies_unauthorized(
        self,
        request,
        client_fixture,
        expected_status,
        mock_room_service,
        create_payload,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.post("/rooms", json=create_payload)

        assert response.status_code == expected_status
        mock_room_service.create_room.assert_not_called()

    def test_create_room_returns_401_with_invalid_token(
        self, invalid_token_client, mock_room_service, create_payload
    ):
        response = invalid_token_client.post(
            "/rooms",
            json=create_payload,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_room_service.create_room.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.room_router
class TestRoomUpdateResponse:
    """PATCH /rooms/{room_id}"""

    def test_update_room_returns_200_and_updated_room(
        self, admin_client, mock_room_service, update_payload
    ):
        response = admin_client.patch("/rooms/r1", json=update_payload)

        assert response.status_code == 200
        mock_room_service.update_room.assert_called_once()

    def test_update_room_returns_404_when_not_found(
        self, admin_client, mock_room_service, update_payload
    ):
        mock_room_service.update_room.side_effect = NotFoundError("Комната", "missing")

        response = admin_client.patch("/rooms/missing", json=update_payload)

        assert response.status_code == 404

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_update_room_denies_unauthorized(
        self,
        request,
        client_fixture,
        expected_status,
        mock_room_service,
        update_payload,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.patch("/rooms/r1", json=update_payload)

        assert response.status_code == expected_status
        mock_room_service.update_room.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.room_router
class TestRoomDeleteResponse:
    """DELETE /rooms/{room_id}"""

    def test_delete_room_returns_204(self, admin_client, mock_room_service):
        response = admin_client.delete("/rooms/r1")

        assert response.status_code == 204
        assert response.content == b""
        mock_room_service.delete_room.assert_called_once_with(room_id="r1")

    def test_delete_room_returns_404_when_not_found(
        self, admin_client, mock_room_service
    ):
        mock_room_service.delete_room.side_effect = NotFoundError("Комната", "missing")

        response = admin_client.delete("/rooms/missing")

        assert response.status_code == 404

    @pytest.mark.parametrize("client_fixture,expected_status", AUTH_DENIAL_CASES_ADMIN)
    def test_delete_room_denies_unauthorized(
        self, request, client_fixture, expected_status, mock_room_service
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.delete("/rooms/r1")

        assert response.status_code == expected_status
        mock_room_service.delete_room.assert_not_called()

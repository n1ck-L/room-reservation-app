from unittest.mock import ANY

import pytest

from app.services.exceptions import ForbiddenError, NotFoundError
from tests.unit.routers.conftest import AUTH_DENIAL_CASES_NO_ADMIN


@pytest.fixture
def create_payload():
    return {
        "room_id": "r1",
        "user_id": "employee-id",
        "start_time": "2026-07-23T09:00:00",
        "end_time": "2026-07-23T10:00:00",
    }


@pytest.fixture
def update_payload():
    return {"end_time": "2026-07-23T11:00:00"}


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.reservation_router
class TestReservationsGetResponse:
    """GET /reservations"""

    def test_get_reservations_returns_list(
        self, employee_client, mock_reservation_service
    ):
        response = employee_client.get("/reservations")

        assert response.status_code == 200
        mock_reservation_service.list_reservations.assert_called_once()

    def test_get_reservations_returns_401_without_auth(
        self, anonymous_client, mock_reservation_service
    ):
        response = anonymous_client.get("/reservations")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers.get("www-authenticate") == "Bearer"
        mock_reservation_service.list_reservations.assert_not_called()

    def test_get_reservations_returns_401_with_invalid_token(
        self, invalid_token_client, mock_reservation_service
    ):
        response = invalid_token_client.get(
            "/reservations",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_reservation_service.list_reservations.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.reservation_router
class TestReservationCreateResponse:
    """POST /reservations"""

    def test_create_reservation_returns_201_and_created_reservation(
        self, employee_client, mock_reservation_service, create_payload
    ):
        response = employee_client.post("/reservations", json=create_payload)

        assert response.status_code == 201
        mock_reservation_service.create_reservation.assert_called_once()

    def test_create_reservation_returns_403_when_forbidden(
        self, employee_client, mock_reservation_service, create_payload
    ):
        mock_reservation_service.create_reservation.side_effect = ForbiddenError(
            "Нет доступа к этой брони"
        )

        response = employee_client.post("/reservations", json=create_payload)

        assert response.status_code == 403
        assert response.json()["detail"] == "Нет доступа к этой брони"

    def test_create_reservation_returns_404_when_room_not_found(
        self, employee_client, mock_reservation_service, create_payload
    ):
        mock_reservation_service.create_reservation.side_effect = NotFoundError(
            "Комната", "missing"
        )

        response = employee_client.post("/reservations", json=create_payload)

        assert response.status_code == 404

    def test_create_reservation_returns_422_when_invalid(
        self, employee_client, mock_reservation_service, create_payload
    ):
        mock_reservation_service.create_reservation.side_effect = ValueError(
            "start_time должен быть раньше end_time"
        )

        response = employee_client.post("/reservations", json=create_payload)

        assert response.status_code == 422
        assert response.json()["detail"] == "start_time должен быть раньше end_time"

    @pytest.mark.parametrize(
        "client_fixture,expected_status", AUTH_DENIAL_CASES_NO_ADMIN
    )
    def test_create_reservation_denies_unauthorized(
        self,
        request,
        client_fixture,
        expected_status,
        mock_reservation_service,
        create_payload,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.post("/reservations", json=create_payload)

        assert response.status_code == expected_status
        mock_reservation_service.create_reservation.assert_not_called()

    def test_create_reservation_returns_401_with_invalid_token(
        self, invalid_token_client, mock_reservation_service, create_payload
    ):
        response = invalid_token_client.post(
            "/reservations",
            json=create_payload,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_reservation_service.create_reservation.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.reservation_router
class TestReservationUpdateResponse:
    """PATCH /reservations/{reservation_id}"""

    def test_update_reservation_returns_200_and_updated_reservation(
        self, employee_client, mock_reservation_service, update_payload
    ):
        response = employee_client.patch("/reservations/res1", json=update_payload)

        assert response.status_code == 200
        mock_reservation_service.update_reservation.assert_called_once()

    def test_update_reservation_returns_403_when_forbidden(
        self, employee_client, mock_reservation_service, update_payload
    ):
        mock_reservation_service.update_reservation.side_effect = ForbiddenError(
            "Нет доступа к этой брони"
        )

        response = employee_client.patch("/reservations/res1", json=update_payload)

        assert response.status_code == 403
        assert response.json()["detail"] == "Нет доступа к этой брони"

    def test_update_reservation_returns_404_when_not_found(
        self, employee_client, mock_reservation_service, update_payload
    ):
        mock_reservation_service.update_reservation.side_effect = NotFoundError(
            "Бронь", "missing"
        )

        response = employee_client.patch("/reservations/missing", json=update_payload)

        assert response.status_code == 404

    def test_update_reservation_returns_422_when_invalid(
        self, employee_client, mock_reservation_service, update_payload
    ):
        mock_reservation_service.update_reservation.side_effect = ValueError(
            "start_time должен быть раньше end_time"
        )

        response = employee_client.patch("/reservations/res1", json=update_payload)

        assert response.status_code == 422
        assert response.json()["detail"] == "start_time должен быть раньше end_time"

    @pytest.mark.parametrize(
        "client_fixture,expected_status", AUTH_DENIAL_CASES_NO_ADMIN
    )
    def test_update_reservation_denies_unauthorized(
        self,
        request,
        client_fixture,
        expected_status,
        mock_reservation_service,
        update_payload,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.patch("/reservations/res1", json=update_payload)

        assert response.status_code == expected_status
        mock_reservation_service.update_reservation.assert_not_called()

    def test_update_reservation_returns_401_with_invalid_token(
        self, invalid_token_client, mock_reservation_service, update_payload
    ):
        response = invalid_token_client.patch(
            "/reservations/res1",
            json=update_payload,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_reservation_service.update_reservation.assert_not_called()


@pytest.mark.unit
@pytest.mark.router
@pytest.mark.reservation_router
class TestReservationDeleteResponse:
    """DELETE /reservations/{reservation_id}"""

    def test_delete_reservation_returns_204(
        self, employee_client, mock_reservation_service
    ):
        response = employee_client.delete("/reservations/res1")

        assert response.status_code == 204
        assert response.content == b""
        mock_reservation_service.delete_reservation.assert_called_once_with(
            reservation_id="res1", current_user=ANY
        )

    def test_delete_reservation_returns_403_when_forbidden(
        self, employee_client, mock_reservation_service
    ):
        mock_reservation_service.delete_reservation.side_effect = ForbiddenError(
            "Нет доступа к этой брони"
        )

        response = employee_client.delete("/reservations/res1")

        assert response.status_code == 403
        assert response.json()["detail"] == "Нет доступа к этой брони"

    def test_delete_reservation_returns_404_when_not_found(
        self, employee_client, mock_reservation_service
    ):
        mock_reservation_service.delete_reservation.side_effect = NotFoundError(
            "Бронь", "missing"
        )

        response = employee_client.delete("/reservations/missing")

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "client_fixture,expected_status", AUTH_DENIAL_CASES_NO_ADMIN
    )
    def test_delete_reservation_denies_unauthorized(
        self, request, client_fixture, expected_status, mock_reservation_service
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.delete("/reservations/res1")

        assert response.status_code == expected_status
        mock_reservation_service.delete_reservation.assert_not_called()

    def test_delete_reservation_returns_401_with_invalid_token(
        self, invalid_token_client, mock_reservation_service
    ):
        response = invalid_token_client.delete(
            "/reservations/res1",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Невалидный токен"
        mock_reservation_service.delete_reservation.assert_not_called()

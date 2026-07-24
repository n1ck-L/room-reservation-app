from datetime import datetime

from fastapi import FastAPI, Query
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.routers.auth import router as auth_router
from app.api.routers.reservation import router as reservation_router
from app.api.routers.room import router as room_router
from app.api.routers.user import router as user_router
from app.api.dependencies import (
    get_auth_service,
    get_current_user,
    get_room_service,
    get_user_service,
    get_reservation_service,
    require_admin,
)
from app.schemas.auth import TokenSchema
from app.schemas.reservation import ReservationSchema
from app.schemas.room import RoomSchema
from app.services.exceptions import UnauthorizedError
from app.schemas.user import CurrentUserSchema, UserRole, UserSchema


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(user_router)
    test_app.include_router(room_router)
    test_app.include_router(reservation_router)
    test_app.include_router(auth_router)
    return test_app


# Service mocks

@pytest.fixture
def mock_service(mocker):
    def _make(**kwargs):
        service = mocker.MagicMock()
        for method_name, return_value in kwargs.items():
            getattr(service, method_name).return_value = return_value
        return service

    return _make


@pytest.fixture
def mock_user_service(mock_service):
    test_data = UserSchema(
                    id="u1",
                    email="a@example.com",
                    login="alice",
                    password=SecretStr("password"),
                    role=UserRole.EMPLOYEE,
                )

    return mock_service(
        list_users=[test_data],
        create_user=test_data,
        update_user=test_data,
        delete_user=None,
    )


@pytest.fixture
def mock_room_service(mock_service):
    room_test = RoomSchema(id="r1", number=1, capacity=1, location="a", equipment=["a", "b"])
    return mock_service(
        list_rooms=[room_test],
        create_room=room_test,
        update_room=room_test,
        delete_room=None,
    )


@pytest.fixture
def mock_reservation_service(mock_service):
    reservation_test = ReservationSchema(
        id="res1",
        room_id="r1",
        user_id="employee-id",
        start_time=datetime(2026, 7, 23, 9, 0),
        end_time=datetime(2026, 7, 23, 10, 0),
    )
    return mock_service(
        list_reservations=[reservation_test],
        create_reservation=reservation_test,
        update_reservation=reservation_test,
        delete_reservation=None,
    )

@pytest.fixture
def mock_auth_service(mock_service):
    token_test = TokenSchema(access_token="access-token", refresh_token="refresh-token")
    return mock_service(
        login=token_test,
        refresh_token=token_test,
        revoke_token=None,
    )


# Auth identities

@pytest.fixture
def admin_user():
    return CurrentUserSchema(id="admin-id", role=UserRole.ADMIN)


@pytest.fixture
def employee_user():
    return CurrentUserSchema(id="employee-id", role=UserRole.EMPLOYEE)


# Test clients

@pytest.fixture
def override_services(app, mock_user_service, mock_room_service, mock_reservation_service, mock_auth_service):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_room_service] = lambda: mock_room_service
    app.dependency_overrides[get_reservation_service] = lambda: mock_reservation_service
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    return app


@pytest.fixture
def admin_client(override_services, admin_user):
    override_services.dependency_overrides[require_admin] = lambda: admin_user
    override_services.dependency_overrides[get_current_user] = lambda: admin_user

    with TestClient(override_services) as test_client:
        yield test_client

    override_services.dependency_overrides.clear()


@pytest.fixture
def employee_client(override_services, employee_user):
    override_services.dependency_overrides[get_current_user] = lambda: employee_user

    with TestClient(override_services) as test_client:
        yield test_client

    override_services.dependency_overrides.clear()


@pytest.fixture
def anonymous_client(override_services):
    with TestClient(override_services) as test_client:
        yield test_client

    override_services.dependency_overrides.clear()


@pytest.fixture
def invalid_token_client(override_services, mocker):
    mock_auth_service = mocker.MagicMock()
    mock_auth_service.get_current_user.side_effect = UnauthorizedError(
        "Невалидный токен"
    )

    override_services.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    with TestClient(override_services) as test_client:
        yield test_client

    override_services.dependency_overrides.clear()


@pytest.fixture
def validation_error_client(override_services, admin_user):
    def get_current_user_with_required_query(
        _: int = Query(required=True, ge=1),
    ) -> CurrentUserSchema:
        return admin_user

    override_services.dependency_overrides[get_current_user] = get_current_user_with_required_query

    with TestClient(override_services) as test_client:
        yield test_client

    override_services.dependency_overrides.clear()


# Shared auth-denial data

AUTH_DENIAL_CASES_ADMIN = [
    ("employee_client", 403),
    ("anonymous_client", 401),
    ("invalid_token_client", 401),
]

AUTH_DENIAL_CASES_NO_ADMIN = [
    ("anonymous_client", 401),
    ("invalid_token_client", 401),
]
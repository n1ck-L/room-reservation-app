from datetime import datetime

import pytest

from app.models.refresh_token import RefreshTokenORM
from app.repositories.refresh_token import RefreshTokenRepository


@pytest.fixture
def repo(mock_db):
    return RefreshTokenRepository(mock_db)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.token_repository
class TestCreate:
    def test_creates_instance_with_given_fields(self, repo, mock_db, mocker):
        expires_at = datetime(2026, 8, 1, 12, 0)

        result = repo.create(
            user_id="user-1",
            token="abc123",
            expires_at=expires_at,
            is_revoked=False,
        )

        assert result is not None
        assert isinstance(result, RefreshTokenORM)
        assert result.user_id == "user-1"
        assert result.token == "abc123"
        assert result.expires_at == expires_at
        assert result.is_revoked is False

    def test_repo_adds_new_instance_to_session(self, repo, mock_db, mocker):
        result = repo.create(
            user_id="user-2",
            token="xyz789",
            expires_at=datetime(2026, 8, 2, 9, 0),
            is_revoked=True,
        )

        mock_db.add.assert_called_once_with(result)


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.token_repository
class TestGetByToken:
    def test_builds_query_filtered_by_token_and_returns_match(
        self, repo, mock_db, mocker
    ):
        mock_select = mocker.patch("app.repositories.refresh_token.select")
        expected = RefreshTokenORM(
            user_id="id",
            token="token",
            expires_at=datetime(2026, 8, 2, 9, 0),
            is_revoked=False,
        )
        query = mock_select.return_value.where.return_value
        mock_db.scalars.return_value.first.return_value = expected

        result = repo.get_by_token("found-token")

        mock_select.assert_called_once_with(RefreshTokenORM)
        mock_select.return_value.where.assert_called_once()
        mock_db.scalars.assert_called_once_with(query)
        mock_db.scalars.return_value.first.assert_called_once_with()
        assert result is expected

    def test_returns_none_when_token_not_found(self, repo, mock_db, mocker):
        mocker.patch("app.repositories.refresh_token.select")
        mock_db.scalars.return_value.first.return_value = None

        result = repo.get_by_token("missing")

        assert result is None

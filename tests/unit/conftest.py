import pytest


@pytest.fixture
def mock_db(mocker):
    return mocker.MagicMock()

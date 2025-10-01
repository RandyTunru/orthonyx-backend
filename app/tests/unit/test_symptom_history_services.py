import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.symptoms_history_services import get_symptom_history
from app.models.symptoms import StatusEnum
import datetime

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_dependencies_factory(mocker):
    def _create_mocks(user_id_to_mock: str, has_history: bool = True):
        mock_user = MagicMock()
        mock_user.id = user_id_to_mock
        mock_user.api_key_enc = "encrypted_api_key"

        mock_get_user_by_id = mocker.patch(
            "app.services.symptoms_history_services.get_user_by_id",
            new_callable=AsyncMock,
            return_value=mock_user
        )

        symptom_data = []
        if has_history:
            mock_symptom_check_1 = MagicMock()
            mock_symptom_check_1.id = "1"
            mock_symptom_check_1.analysis = "Analysis 1"
            mock_symptom_check_1.status = StatusEnum.completed
            mock_symptom_check_1.submitted_at = "2023-10-01T12:00:00Z"
            mock_symptom_check_1.age = 30
            mock_symptom_check_1.sex = "male"
            mock_symptom_check_1.symptoms = "cough, fever"
            mock_symptom_check_1.duration = "2 days"
            mock_symptom_check_1.severity = 3
            mock_symptom_check_1.additional_notes = "None"
            mock_symptom_check_1.user_id = user_id_to_mock

            mock_symptom_check_2 = MagicMock()
            mock_symptom_check_2.id = "2"
            mock_symptom_check_2.analysis = "Analysis 2"
            mock_symptom_check_2.status = StatusEnum.completed
            mock_symptom_check_2.submitted_at = "2023-10-02T12:00:00Z"
            mock_symptom_check_2.age = 25
            mock_symptom_check_2.sex = "female"
            mock_symptom_check_2.symptoms = "headache"
            mock_symptom_check_2.duration = "1 day"
            mock_symptom_check_2.severity = 2
            mock_symptom_check_2.additional_notes = "Allergic to penicillin"
            mock_symptom_check_2.user_id = user_id_to_mock
            
            symptom_data = [mock_symptom_check_1, mock_symptom_check_2]

        mock_decrypt = mocker.patch(
            'app.services.symptoms_history_services.decrypt_api_key',
            return_value='decrypted_raw_api_key'
        )

        mock_get_symptom_by_id = mocker.patch(
            "app.services.symptoms_history_services.get_symptom_checkby_user_id",
            new_callable=AsyncMock,
            return_value=symptom_data
        )

        mock_db = AsyncMock()

        return {
            "db": mock_db,
            "get_user_by_id": mock_get_user_by_id,
            "get_symptom_by_id": mock_get_symptom_by_id,
            "decrypt_api_key": mock_decrypt,
            "user_data": mock_user
        }
    
    return _create_mocks


# --- Updated Tests ---

async def test_get_symptom_history_success(mock_dependencies_factory):
    mocks = mock_dependencies_factory(user_id_to_mock="1", has_history=True)

    result = await get_symptom_history(
        db=mocks["db"],
        user_id="1",
        api_key="decrypted_raw_api_key"
    )

    assert len(result) == 2
    mocks["get_user_by_id"].assert_awaited_once_with(mocks["db"], "1")
    mocks["decrypt_api_key"].assert_called_once_with("encrypted_api_key")
    mocks["get_symptom_by_id"].assert_awaited_once_with(mocks["db"], user_id="1", limit=10, offset=0)


async def test_get_symptom_history_no_history(mock_dependencies_factory):
    mocks = mock_dependencies_factory(user_id_to_mock="2", has_history=False)
    
    result = await get_symptom_history(
        db=mocks["db"],
        user_id="2",
        api_key="decrypted_raw_api_key"
    )

    assert len(result) == 0
    mocks["get_user_by_id"].assert_awaited_once_with(mocks["db"], "2")
    mocks["decrypt_api_key"].assert_called_once_with("encrypted_api_key")
    mocks["get_symptom_by_id"].assert_awaited_once_with(mocks["db"], user_id="2", limit=10, offset=0)


async def test_get_symptom_history_invalid_user(mock_dependencies_factory):
    mocks = mock_dependencies_factory(user_id_to_mock="invalid_user")
    mocks["get_user_by_id"].return_value = None 

    with pytest.raises(ValueError, match="invalid_user"):
        await get_symptom_history(
            db=mocks["db"],
            user_id="invalid_user",
            api_key="decrypted_raw_api_key"
        )

    mocks["get_user_by_id"].assert_awaited_once_with(mocks["db"], "invalid_user")
    mocks["decrypt_api_key"].assert_not_called()
    mocks["get_symptom_by_id"].assert_not_awaited()


async def test_get_symptom_history_invalid_api_key(mock_dependencies_factory):
    mocks = mock_dependencies_factory(user_id_to_mock="1")

    with pytest.raises(ValueError, match="invalid_api_key"):
        await get_symptom_history(
            db=mocks["db"],
            user_id="1",
            api_key="wrong_api_key" 
        )

    mocks["get_user_by_id"].assert_awaited_once_with(mocks["db"], "1")
    mocks["decrypt_api_key"].assert_called_once_with("encrypted_api_key")
    mocks["get_symptom_by_id"].assert_not_awaited()
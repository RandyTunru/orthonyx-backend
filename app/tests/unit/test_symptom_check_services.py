import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.symptoms_check_service import process_symptom_check
from app.models.symptoms import StatusEnum 

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_dependencies(mocker):
 
    mock_user = MagicMock()
    mock_user.id = "1"
    mock_user.api_key_enc = "encrypted_api_key"
    
    mock_get_user_by_id = mocker.patch(
        "app.services.symptoms_check_service.get_user_by_id", 
        new_callable=AsyncMock, 
        return_value=mock_user
    )

    mock_symptom_check = MagicMock()
    mock_symptom_check.id = "1"
    mock_symptom_check.analysis = None 
    mock_symptom_check.status = StatusEnum.not_completed
    
    mock_submit_symptom_check = mocker.patch(
        "app.services.symptoms_check_service.submit_symptom_check",
        new_callable=AsyncMock,
        return_value=mock_symptom_check
    )

    mock_decrypt = mocker.patch(
        'app.services.symptoms_check_service.decrypt_api_key', 
        return_value='decrypted_raw_api_key'
    )
    
    mock_db = AsyncMock()
    
    mock_result_object = MagicMock()
  
    mock_result_object.scalars.return_value.first.return_value = mock_user
    
    mock_db.execute.return_value = mock_result_object


    return {
        "db": mock_db,
        "get_user_by_id": mock_get_user_by_id,
        "submit_symptom_check": mock_submit_symptom_check,
        "decrypt_api_key": mock_decrypt,
        "user_data": mock_user,
        "symptom_data": mock_symptom_check
    }


async def test_process_symptom_check_success(mock_dependencies):
    # Call the service with valid data
    result = await process_symptom_check(
        db=mock_dependencies["db"],
        user_id="1",
        api_key="decrypted_raw_api_key",
        age=30,
        sex="male",
        symptoms="cough, fever",
        duration="3 days",
        severity=2,
        additional_notes="Patient has a history of asthma."
    )
    
    # Assert that the final object has been updated correctly
    assert result.analysis is not None
    assert result.status == StatusEnum.completed
    
    # Assert that our mocked functions were called correctly
    mock_dependencies["get_user_by_id"].assert_awaited_once_with(mock_dependencies["db"], "1")
    mock_dependencies["decrypt_api_key"].assert_called_once_with("encrypted_api_key")
    mock_dependencies["submit_symptom_check"].assert_awaited_once()
    
    # Assert that the transaction was committed
    mock_dependencies["db"].commit.assert_awaited_once()


async def test_process_symptom_check_invalid_user(mock_dependencies):
    # Configure the mock to simulate "user not found"
    mock_dependencies["get_user_by_id"].return_value = None

    with pytest.raises(ValueError, match="invalid_user"):
        await process_symptom_check(
            db=mock_dependencies["db"], user_id="999", api_key="any_key", age=30, sex="male",
            symptoms="cough", duration="1 day", severity=1
        )

    # Assert that the process stopped early
    mock_dependencies["decrypt_api_key"].assert_not_called()
    mock_dependencies["submit_symptom_check"].assert_not_awaited()
    mock_dependencies["db"].commit.assert_not_awaited()


async def test_process_symptom_check_invalid_api_key(mock_dependencies):
    with pytest.raises(ValueError, match="invalid_api_key"):
        await process_symptom_check(
            db=mock_dependencies["db"], user_id="1", api_key="invalid_api_key", age=30, sex="male",
            symptoms="cough", duration="1 day", severity=1
        )
    
    # Assert that the process stopped after checking the key
    mock_dependencies["get_user_by_id"].assert_awaited_once()
    mock_dependencies["decrypt_api_key"].assert_called_once()
    mock_dependencies["submit_symptom_check"].assert_not_awaited()
    mock_dependencies["db"].commit.assert_not_awaited()
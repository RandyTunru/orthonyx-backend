import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from app.services.auth_service import register_user, signin_and_rotate_api_key

# Mark all tests in this file as asyncio tests
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db():
    """
    Provides a mock AsyncSession with a correctly configured synchronous `begin`
    method that returns an async context manager.
    """
    # 1. The mock for the object that `async with` will use.
    #    This part is correct and defines the async context manager protocol.
    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock()
    context_manager.__aexit__ = AsyncMock()

    # 2. The main mock for the `db: AsyncSession` object.
    db_session_mock = AsyncMock()

    # 3. Add a synchronous `begin` method to the mock session.
    db_session_mock.begin = MagicMock()

    # 4. Configure the synchronous mock to return our async context manager.
    db_session_mock.begin.return_value = context_manager

    return db_session_mock

@pytest.fixture
def mock_security_utils(mocker):
    """Mocks all functions in the security utility module."""
    # Using a dictionary to hold mock objects makes them easy to access in tests
    mocks = {
        'hash_password': mocker.patch('app.services.auth_service.hash_password', return_value='hashed_password_string'),
        'verify_password': mocker.patch('app.services.auth_service.verify_password', return_value=True),
        'generate_api_key_hex': mocker.patch('app.services.auth_service.generate_api_key_hex', return_value='new_raw_api_key'),
        'encrypt_api_key': mocker.patch('app.services.auth_service.encrypt_api_key', return_value='encrypted_api_key'),
        'decrypt_api_key': mocker.patch('app.services.auth_service.decrypt_api_key', return_value='decrypted_raw_api_key'),
        'api_key_expiration_from_now': mocker.patch('app.services.auth_service.api_key_expiration_from_now', return_value=datetime.now(timezone.utc) + timedelta(days=30))
    }
    return mocks

@pytest.fixture
def mock_crud_user(mocker):
    """Mocks all functions in the user CRUD module."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = 'testuser'
    mock_user.email = 'test@example.com'
    mock_user.password_hash = 'hashed_password_string'
    mock_user.api_key_enc = 'old_encrypted_key'
    mock_user.api_key_expires_at = datetime.now(timezone.utc) + timedelta(days=10) # For reuse case
    
    mocks = {
        'get_user_by_username': mocker.patch('app.services.auth_service.get_user_by_username', return_value=None),
        'get_user_by_username_for_update': mocker.patch('app.services.auth_service.get_user_by_username_for_update', return_value=mock_user),
        'get_user_by_email': mocker.patch('app.services.auth_service.get_user_by_email', return_value=None),
        'create_user': mocker.patch('app.services.auth_service.create_user', return_value=mock_user),
        'rotate_api_key': mocker.patch('app.services.auth_service.rotate_api_key', return_value=mock_user),
        'update_last_login': mocker.patch('app.services.auth_service.update_last_login', return_value=mock_user),
        'mock_user_instance': mock_user
    }
    return mocks

# --- Tests for register_user ---

async def test_register_user_success(mock_db, mock_security_utils, mock_crud_user):
    """
    GIVEN valid and unique user details
    WHEN register_user is called
    THEN a new user is created and security functions are called correctly
    """
    # Arrange
    email = "new@example.com"
    username = "newuser"
    password = "password123"

    # Act
    await register_user(mock_db, email, username, password)

    # Assert
    # Check that uniqueness checks were performed
    mock_crud_user['get_user_by_username'].assert_called_once_with(mock_db, username)
    mock_crud_user['get_user_by_email'].assert_called_once_with(mock_db, email)

    # Check that security functions were called
    mock_security_utils['hash_password'].assert_called_once_with(password)
    mock_security_utils['generate_api_key_hex'].assert_called_once()
    mock_security_utils['encrypt_api_key'].assert_called_once_with('new_raw_api_key')

    # Check that the user was created with the correct, processed data
    mock_crud_user['create_user'].assert_called_once()
    # Get the arguments passed to create_user
    call_args, call_kwargs = mock_crud_user['create_user'].call_args
    assert call_kwargs['email'] == email
    assert call_kwargs['username'] == username
    assert call_kwargs['password_hash'] == 'hashed_password_string'
    assert call_kwargs['api_key_enc'] == 'encrypted_api_key'
    assert 'api_key_expires_at' in call_kwargs

async def test_register_user_username_exists(mock_db, mock_crud_user):
    """
    GIVEN a username that already exists
    WHEN register_user is called
    THEN a ValueError is raised and user is not created
    """
    # Arrange: Simulate that the username is found
    mock_crud_user['get_user_by_username'].return_value = MagicMock()

    # Act & Assert
    with pytest.raises(ValueError, match="username_exists"):
        await register_user(mock_db, "test@example.com", "existinguser", "password123")
    
    # Ensure no attempt was made to create a user
    mock_crud_user['create_user'].assert_not_called()

# --- Tests for signin_and_rotate_api_key ---

async def test_signin_success_and_rotate_key(mock_db, mock_security_utils, mock_crud_user):
    """
    GIVEN correct credentials for a user whose key needs rotation
    WHEN signin_and_rotate_api_key is called
    THEN a new API key is generated and returned
    """
    # Arrange: Force key rotation by making the 'expires_at' date in the past
    user = mock_crud_user['mock_user_instance']
    user.api_key_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    mock_crud_user['get_user_by_username_for_update'].return_value = user

    # Act
    updated_user, raw_key = await signin_and_rotate_api_key(mock_db, "testuser", "correct_password")

    # Assert
    assert updated_user is not None
    assert raw_key == 'new_raw_api_key' # The newly generated key
    mock_security_utils['verify_password'].assert_called_once_with("correct_password", user.password_hash)
    mock_crud_user['rotate_api_key'].assert_called_once()
    mock_security_utils['decrypt_api_key'].assert_not_called() # Should skip this path

async def test_signin_success_and_reuse_key(mock_db, mock_security_utils, mock_crud_user):
    """
    GIVEN correct credentials for a user with a valid, unexpired key
    WHEN signin_and_rotate_api_key is called
    THEN the existing API key is decrypted and returned
    """
    # Arrange: The default fixture setup has a future 'expires_at' date, so it will enter the reuse block.
    
    # Act
    updated_user, raw_key = await signin_and_rotate_api_key(mock_db, "testuser", "correct_password")

    # Assert
    assert updated_user is not None
    assert raw_key == 'decrypted_raw_api_key' # The reused key
    mock_security_utils['verify_password'].assert_called_once()
    mock_security_utils['decrypt_api_key'].assert_called_once_with(mock_crud_user['mock_user_instance'].api_key_enc)
    mock_crud_user['update_last_login'].assert_called_once()
    mock_crud_user['rotate_api_key'].assert_not_called() # Should NOT rotate

async def test_signin_failure_user_not_found(mock_db, mock_crud_user):
    """

    GIVEN a username that does not exist
    WHEN signin_and_rotate_api_key is called
    THEN it returns (None, None)
    """
    # Arrange: Simulate user not found
    mock_crud_user['get_user_by_username_for_update'].return_value = None

    # Act
    user, key = await signin_and_rotate_api_key(mock_db, "nouser", "password")

    # Assert
    assert user is None
    assert key is None

async def test_signin_failure_wrong_password(mock_db, mock_security_utils, mock_crud_user):
    """
    GIVEN an existing username but an incorrect password
    WHEN signin_and_rotate_api_key is called
    THEN it returns (None, None)
    """
    # Arrange: Simulate password verification failure
    mock_security_utils['verify_password'].return_value = False

    # Act
    user, key = await signin_and_rotate_api_key(mock_db, "testuser", "wrong_password")

    # Assert
    assert user is None
    assert key is None
    mock_security_utils['verify_password'].assert_called_once_with("wrong_password", mock_crud_user['mock_user_instance'].password_hash)
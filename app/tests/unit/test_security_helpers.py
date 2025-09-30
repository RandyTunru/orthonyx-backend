import pytest 
from app.utils.security import hash_password, verify_password, generate_api_key_hex, encrypt_api_key, decrypt_api_key, api_key_expiration_from_now
from datetime import datetime, timezone

def test_password_hashing_and_verification():
    password = "securepassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_api_key_generation_and_encryption():
    api_key = generate_api_key_hex()
    assert len(api_key) == 64  # 32 bytes in hex is 64 characters
    encrypted = encrypt_api_key(api_key)
    assert isinstance(encrypted, str)   
    decrypted = decrypt_api_key(encrypted)
    
    assert decrypted != encrypted  # Ensure encryption changes the string
    assert decrypted == api_key # Ensure decryption returns the original

def test_decrypt_with_invalid_token():
    invalid_token = "invalidtoken"
    with pytest.raises(ValueError):
        decrypt_api_key(invalid_token)

def test_api_key_expiration():
    expires_at = api_key_expiration_from_now()
    assert expires_at > datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    expires_at_7_days = api_key_expiration_from_now(days=7, start=now)
    assert (expires_at_7_days - now).days == 7

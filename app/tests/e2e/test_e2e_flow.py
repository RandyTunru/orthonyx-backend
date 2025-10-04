import pytest
import asyncio
import uuid
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

# A helper to generate unique user data for each test run
def generate_unique_user():
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"e2e_user_{unique_id}",
        "email": f"e2e_user_{unique_id}@example.com",
        "password": "strongpassword123"
    }

async def test_full_workflow(api_client):
    """
    Tests the complete user journey: signup -> signin -> symptom check -> get history.
    """
    user_data = generate_unique_user()
    api_key = None

    # 1. Signup
    async with api_client.post("/auth/signup", json=user_data) as resp:
        assert resp.status == 201

    # 2. Signin to get API Key
    async with api_client.post("/auth/signin", json={"username": user_data["username"], "password": user_data["password"]}) as resp:
        assert resp.status == 200
        sign_in_response = await resp.json()
        api_key = sign_in_response["api_key"]
        assert api_key is not None
        user_id = sign_in_response["user_id"]
        assert user_id is not None

    auth_headers = {"X-API-Key": api_key, "X-User-ID": user_id}

    # 3. Submit a symptom check
    symptom_payload = {
        "age": 35, "sex": "male", "symptoms": "headache, fever", 
        "duration": "2 days", "severity": 7, "additional_notes": "No allergies"
    }
    async with api_client.post("/symptom-check/", headers=auth_headers, json=symptom_payload) as resp:
        assert resp.status == 201
        check_response = await resp.json()
        check_data = check_response
        assert check_data["status"] == "completed"
        assert check_data["analysis"] is not None
        
        # Store the ID for the final check
        symptom_check_id = check_data["id"]

    # 4. Get symptom history
    async with api_client.get("/symptom-history/", headers=auth_headers) as resp:
        assert resp.status == 200
        history_data = await resp.json()

        assert history_data["user_id"] == user_id
        assert "history" in history_data

        assert len(history_data["history"]) > 0
        assert history_data["history"][0]["id"] == symptom_check_id
        assert history_data["history"][0]["analysis"] == check_data["analysis"]
        assert history_data["history"][0]["status"] == "completed"

async def test_same_credentials_signup(api_client):
    """Tests that signing up with the same username/email fails."""
    user_data = generate_unique_user()

    # First signup should succeed
    async with api_client.post("/auth/signup", json=user_data) as resp:
        assert resp.status == 201

    # Second signup with same data should fail
    async with api_client.post("/auth/signup", json=user_data) as resp:
        assert resp.status == 400  # Expecting a 400 Bad Request due to duplicate

async def test_wrong_api_key(api_client):
    """Tests that a protected endpoint correctly returns 401 with a wrong key."""
    user_data = generate_unique_user()

    async with api_client.post("/auth/signup", json=user_data) as resp:
        assert resp.status == 201

    async with api_client.post("/auth/signin", json={"username": user_data["username"], "password": user_data["password"]}) as resp:
        assert resp.status == 200
        signin_data = await resp.json()
        user_id = signin_data["user_id"]
        assert user_id is not None

    wrong_api_key = "invalidapikey123"
    auth_headers = {"X-API-Key": wrong_api_key, "X-User-ID": user_id}

    symptom_payload = {
        "age": 30, "sex": "female", "symptoms": "sore throat", 
        "duration": "1 day", "severity": 4
    }

    async with api_client.post("/symptom-check/", headers=auth_headers, json=symptom_payload) as resp:
        assert resp.status == 401

async def test_unauthorized_access_symptom_check(api_client):
    """Tests that a protected endpoint correctly returns 422 without a valid header."""
    symptom_payload = {
        "age": 30, "sex": "female", "symptoms": "sore throat", 
        "duration": "1 day", "severity": 4
    }

    async with api_client.post("/symptom-check/", json=symptom_payload) as resp:
        assert resp.status == 422  # Missing headers should lead to 422 due to validation error

async def test_unauthorized_access_symptom_history(api_client):
    """Tests that a protected endpoint correctly returns 422 without a valid header."""
    async with api_client.get("/symptom-history/") as resp:
        assert resp.status == 422  # Missing headers should lead to 422 due to validation error

async def test_concurrent_sign_up_and_logins(api_client):
    """Demonstrate handling of 3 concurrent sign-ins and sign-ups."""
    user_data_1 = generate_unique_user()
    user_data_2 = generate_unique_user()
    user_data_3 = generate_unique_user()

    async def signup_and_signin(user_data: Dict[str, Any]):
        # Signup
        async with api_client.post("/auth/signup", json=user_data) as resp:
            assert resp.status == 201

        # Signin
        async with api_client.post("/auth/signin", json={"username": user_data["username"], "password": user_data["password"]}) as resp:
            assert resp.status == 200
            signin_data = await resp.json()
            api_key = signin_data["api_key"]
            user_id = signin_data["user_id"]
            return api_key, user_id

    tasks = [
        signup_and_signin(user_data_1),
        signup_and_signin(user_data_2),
        signup_and_signin(user_data_3),
    ]

    results = await asyncio.gather(*tasks)

    for api_key, user_id in results:
        assert api_key is not None
        assert user_id is not None

async def test_concurrent_symptom_checks(api_client):
    """Demonstrates handling of 3 concurrent requests for the same user."""
    user_data = generate_unique_user()
    
    # Setup user and get key
    async with api_client.post("/auth/signup", json=user_data) as resp:
        assert resp.status == 201

    async with api_client.post("/auth/signin", json={"username": user_data["username"], "password": user_data["password"]}) as resp:
        assert resp.status == 200
        signin_data = await resp.json()
        api_key = signin_data["api_key"]
        user_id = signin_data["user_id"]

    auth_headers = {"X-API-Key": api_key, "X-User-ID": user_id}

    # Define the request task
    async def submit_check(payload: Dict[str, Any]):
        async with api_client.post("/symptom-check/", headers=auth_headers, json=payload) as resp:
            assert resp.status == 201
            return resp.status

    # Create a list of 3 distinct payloads
    payloads = [
        {"age": 25, "sex": "male", "symptoms": "cough", "duration": "3 days", "severity": 5},
        {"age": 40, "sex": "female", "symptoms": "fatigue", "duration": "1 week", "severity": 6},
        {"age": 55, "sex": "male", "symptoms": "joint pain", "duration": "5 days", "severity": 7},
    ]
    
    # Create and run 3 tasks concurrently
    tasks = [submit_check(p) for p in payloads]
    results = await asyncio.gather(*tasks)

    print(f"Concurrent request results: {results}")
    
    # Assert that all 3 requests were successful
    assert len(results) == 3
    assert all(status == 201 for status in results)

    async with api_client.get("/symptom-history/", headers=auth_headers) as resp:
        assert resp.status == 200
        history_data = await resp.json()
        assert len(history_data["history"]) >= 3  # At least 3 entries should be present

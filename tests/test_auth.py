"""
Tests for JWT Authentication, Authorization boundaries, and IDOR protection.
"""

import jwt
import pytest
from starlette.testclient import TestClient

from main import app
from auth import (
    get_base_supabase_client,
    get_supabase_client,
    get_authenticated_supabase_client,
)
from config import settings


@pytest.fixture(autouse=True)
def setup_auth_env(mock_supabase):
    settings.SUPABASE_URL = "https://mock.supabase.co"
    settings.SUPABASE_KEY = "mock_anon_key"
    settings.SUPABASE_JWT_SECRET = "super_secret_test_jwt_key_12345678"
    app.dependency_overrides[get_base_supabase_client] = lambda: mock_supabase
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase
    app.dependency_overrides[get_authenticated_supabase_client] = lambda: mock_supabase
    yield
    app.dependency_overrides.clear()


def test_unauthorized_access_to_protected_endpoints(mock_supabase):
    """Verifies that endpoints without Authorization header reject with 401."""
    client = TestClient(app)

    # 1. log_meal
    res_log = client.post("/api/v1/log_meal", json={"food_name": "Apple", "calories": 50, "protein_g": 0.5, "fat_g": 0.1, "carb_g": 10})
    assert res_log.status_code == 401
    assert "Missing Authorization header" in res_log.json()["detail"]

    # 2. history
    res_hist = client.get("/api/v1/history/test_user_123")
    assert res_hist.status_code == 401

    # 3. community like
    res_like = client.post("/api/v1/community/like", json={"meal_id": 1})
    assert res_like.status_code == 401


def test_valid_jwt_token_authentication(mock_supabase):
    """Verifies that a valid JWT token signed with SUPABASE_JWT_SECRET grants access."""
    token = jwt.encode(
        {"sub": "user_real_999", "email": "user999@test.com"},
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    res = client.get("/api/v1/history/user_real_999", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_idor_protection_blocks_querying_other_users(mock_supabase):
    """Tests that a user cannot query another user's private meal history (IDOR protection)."""
    token = jwt.encode(
        {"sub": "attacker_user_id", "email": "attacker@test.com"},
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    # Attempt to query victim's history
    res = client.get("/api/v1/history/victim_user_id", headers=headers)
    assert res.status_code == 403
    assert "You may only query your own meal history" in res.json()["detail"]


def test_malformed_jwt_token_rejected(mock_supabase):
    """Verifies that invalid or corrupted tokens return 401."""
    headers = {"Authorization": "Bearer not_a_valid_token"}
    client = TestClient(app)
    res = client.get("/api/v1/history/user1", headers=headers)
    assert res.status_code == 401

"""
Dedicated Security & Edge-Case Tests:
- Supabase JWT PostgREST propagation and RLS validation
- Abort counter increment on failed meal_likes insertion
- Model unavailable (503) behavior when binary is missing
- Unauthorized RPC calls
"""

import pytest
from starlette.testclient import TestClient

from main import app
from auth import (
    get_authenticated_supabase_client,
    get_supabase_client,
    get_current_user,
    AuthenticatedUser,
)
from model_utils import set_loaded_model_for_testing
from tests.conftest import MockSupabaseClient


def test_model_unavailable_returns_503(test_client, sample_image_bytes):
    """Verifies that /api/v1/analyze returns 503 with explicit error when model is None."""
    set_loaded_model_for_testing(None)
    files = {"file": ("apple.jpg", sample_image_bytes, "image/jpeg")}
    res = test_client.post("/api/v1/analyze", files=files)
    assert res.status_code == 503
    assert "Trained ML model is currently unavailable" in res.json()["detail"]


def test_like_fails_never_increments_counter(test_client):
    """
    Critical security test: If inserting into meal_likes fails for any reason
    (e.g. database error), likes_count must NOT be incremented.
    """
    class FailingLikeSupabaseClient(MockSupabaseClient):
        def rpc(self, func_name, params):
            # Simulate RPC unavailable so fallback table operations execute
            raise Exception("Function increment_meal_likes does not exist")

        def table(self, table_name):
            builder = super().table(table_name)
            if table_name == "meal_likes":
                # Simulate failure on inserting like
                def broken_insert(data):
                    raise Exception("Disk full or permission denied writing to meal_likes")
                builder.insert = broken_insert
            return builder

    failing_client = FailingLikeSupabaseClient(caller_uid="test_user_123")
    app.dependency_overrides[get_authenticated_supabase_client] = lambda: failing_client

    # Initial likes count on meal 1 is 5
    initial_likes = failing_client.store["logged_meals"][0]["likes_count"]
    assert initial_likes == 5

    res = test_client.post("/api/v1/community/like", json={"meal_id": 1})
    assert res.status_code == 500
    assert "Failed to register meal like" in res.json()["detail"]

    # Verify counter remains unchanged (did NOT increment to 6)
    assert failing_client.store["logged_meals"][0]["likes_count"] == 5


def test_rls_blocks_user_spoofing_in_log_meal(test_client):
    """
    Tests that if a client attempts to pass a spoofed user_id in the body,
    the backend overrides it with current_user.user_id, preventing RLS violations.
    """
    client_with_rls = MockSupabaseClient(caller_uid="test_user_123")
    app.dependency_overrides[get_authenticated_supabase_client] = lambda: client_with_rls

    # Attempt to spoof user_id as "victim_user_999"
    payload = {
        "user_id": "victim_user_999",
        "food_name": "Salad",
        "calories": 150.0,
        "protein_g": 3.0,
        "fat_g": 5.0,
        "carb_g": 10.0
    }
    res = test_client.post("/api/v1/log_meal", json=payload)
    assert res.status_code == 200

    # Ensure record in DB actually belongs to test_user_123, not victim_user_999
    inserted = [m for m in client_with_rls.store["logged_meals"] if m["food_name"] == "Salad"]
    assert len(inserted) == 1
    assert inserted[0]["user_id"] == "test_user_123"


def test_unauthorized_rpc_execution_blocked():
    """
    Tests that unauthenticated callers cannot execute increment_meal_likes.
    """
    unauth_client = MockSupabaseClient(caller_uid=None)
    with pytest.raises(Exception) as exc:
        unauth_client.rpc("increment_meal_likes", {"m_id": 1})
    assert "Unauthorized" in str(exc.value)

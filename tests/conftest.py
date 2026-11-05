"""
Pytest configuration and shared fixtures for NutriLens backend testing.
"""

import io
import jwt
from typing import Dict, Any
import pytest
from PIL import Image
from starlette.testclient import TestClient

from main import app, get_http_client
from auth import get_current_user, get_supabase_client, AuthenticatedUser
from config import settings


class MockSupabaseQueryBuilder:
    """Mock query builder simulating chained PostgREST / Supabase calls."""
    def __init__(self, table_name: str, store: Dict[str, Any]):
        self.table_name = table_name
        self.store = store
        self._action = "select"
        self._filters = {}
        self._insert_data = None
        self._update_data = None

    def select(self, *args, **kwargs):
        self._action = "select"
        return self

    def insert(self, data):
        self._action = "insert"
        self._insert_data = data
        return self

    def update(self, data):
        self._action = "update"
        self._update_data = data
        return self

    def delete(self):
        self._action = "delete"
        return self

    def eq(self, column, value):
        self._filters[column] = value
        return self

    def gte(self, column, value):
        self._filters[f"{column}__gte"] = value
        return self

    def order(self, column, desc=False):
        return self

    def limit(self, count):
        return self

    def execute(self):
        class Result:
            def __init__(self, data):
                self.data = data

        table = self.store.setdefault(self.table_name, [])

        if self._action == "insert":
            new_id = len(table) + 1
            if isinstance(self._insert_data, dict):
                item = {"id": new_id, **self._insert_data}
                # Check for duplicate likes in meal_likes
                if self.table_name == "meal_likes":
                    for existing in table:
                        if existing.get("meal_id") == item.get("meal_id") and existing.get("user_id") == item.get("user_id"):
                            raise Exception("duplicate key value violates unique constraint 'uq_meal_user_like'")
                table.append(item)
                return Result([item])
            return Result([])

        elif self._action == "select":
            matched = table
            for col, val in self._filters.items():
                if "__gte" not in col:
                    matched = [row for row in matched if row.get(col) == val]
            return Result(matched)

        elif self._action == "update":
            updated = []
            for row in table:
                matches = all(row.get(col) == val for col, val in self._filters.items() if "__gte" not in col)
                if matches:
                    row.update(self._update_data)
                    updated.append(row)
            return Result(updated)

        return Result([])


class MockSupabaseClient:
    """Mock Supabase Client with in-memory persistence and auth stub."""
    def __init__(self):
        self.store = {
            "logged_meals": [
                {
                    "id": 1,
                    "user_id": "test_user_123",
                    "food_name": "Apple",
                    "calories": 52.0,
                    "protein_g": 0.3,
                    "fat_g": 0.2,
                    "carb_g": 14.0,
                    "is_public": True,
                    "likes_count": 5,
                    "created_at": "2026-11-01T12:00:00Z"
                },
                {
                    "id": 2,
                    "user_id": "other_user_456",
                    "food_name": "Banana",
                    "calories": 89.0,
                    "protein_g": 1.1,
                    "fat_g": 0.3,
                    "carb_g": 23.0,
                    "is_public": False,
                    "likes_count": 0,
                    "created_at": "2026-11-02T12:00:00Z"
                }
            ],
            "meal_likes": [],
            "shopping_list": []
        }

    def table(self, table_name: str):
        return MockSupabaseQueryBuilder(table_name, self.store)

    def rpc(self, func_name: str, params: Dict[str, Any]):
        class RPCResult:
            def __init__(self, data):
                self.data = data
            def execute(self):
                return self

        if func_name == "increment_meal_likes":
            m_id = params.get("m_id")
            for m in self.store["logged_meals"]:
                if m["id"] == m_id:
                    m["likes_count"] += 1
                    return RPCResult(m["likes_count"])
            return RPCResult(1)

        elif func_name == "get_top_loggers_last_7_days":
            return RPCResult([
                {"rank": 1, "user_id": "test_user_123", "score": 10},
                {"rank": 2, "user_id": "other_user_456", "score": 5},
                {"rank": 3, "user_id": None, "score": 0}
            ])
        return RPCResult(None)


@pytest.fixture
def mock_supabase():
    return MockSupabaseClient()


@pytest.fixture
def test_user():
    return AuthenticatedUser(
        user_id="test_user_123",
        email="test@nutrilens.dev",
        claims={"role": "authenticated"}
    )


@pytest.fixture
def test_client(mock_supabase, test_user):
    # Configure JWT secret for test offline validation
    settings.SUPABASE_JWT_SECRET = "test_secret_key_12345678901234567890"

    # Dependency overrides
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: test_user

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes():
    """Generates a small in-memory valid RGB test image in JPEG format."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

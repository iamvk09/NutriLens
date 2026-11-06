"""
API Endpoints Integration and Functional Tests.
"""

import json
from unittest.mock import patch, AsyncMock
import pytest
import httpx
from starlette.testclient import TestClient

from main import app, get_http_client
from config import settings


def test_root_and_health_endpoints(test_client):
    """Tests / and /health status reporting."""
    res_root = test_client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["app"] == "NutriLens API"

    res_health = test_client.get("/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_analyze_food_image(test_client, sample_image_bytes):
    """Tests /api/v1/analyze with valid image upload using mocked USDA nutrition client."""
    fake_usda_response = {
        "foods": [
            {
                "foodNutrients": [
                    {"nutrientId": 1008, "nutrientName": "Energy", "value": 95.0},
                    {"nutrientId": 1003, "nutrientName": "Protein", "value": 0.5},
                    {"nutrientId": 1004, "nutrientName": "Total lipid (fat)", "value": 0.3},
                    {"nutrientId": 1005, "nutrientName": "Carbohydrate, by difference", "value": 25.0},
                ]
            }
        ]
    }

    class MockUSDAAsyncClient:
        async def get(self, url, **kwargs):
            class MockResponse:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return fake_usda_response
            return MockResponse()

    old_usda_key = settings.USDA_API_KEY
    settings.USDA_API_KEY = "test_mock_usda_key"
    app.dependency_overrides[get_http_client] = lambda: MockUSDAAsyncClient()
    try:
        files = {"file": ("test_apple.jpg", sample_image_bytes, "image/jpeg")}
        res = test_client.post("/api/v1/analyze", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "food_name" in data
        assert "calories" in data
        assert "protein_g" in data
        assert "fat_g" in data
        assert "carb_g" in data
        assert data["calories"] == 95.0
        assert data["protein_g"] == 0.5
        assert data["fat_g"] == 0.3
        assert data["carb_g"] == 25.0
    finally:
        settings.USDA_API_KEY = old_usda_key
        app.dependency_overrides.pop(get_http_client, None)


def test_analyze_food_image_usda_failure(test_client, sample_image_bytes):
    """Tests /api/v1/analyze handles external USDA API failures properly by returning 502."""
    class FailingUSDAAsyncClient:
        async def get(self, url, **kwargs):
            request = httpx.Request("GET", url)
            response = httpx.Response(500, request=request)
            raise httpx.HTTPStatusError("USDA Server Error", request=request, response=response)

    old_usda_key = settings.USDA_API_KEY
    settings.USDA_API_KEY = "test_mock_usda_key"
    app.dependency_overrides[get_http_client] = lambda: FailingUSDAAsyncClient()
    try:
        files = {"file": ("test_apple.jpg", sample_image_bytes, "image/jpeg")}
        res = test_client.post("/api/v1/analyze", files=files)
        assert res.status_code == 502
        assert "Failed to retrieve nutritional data" in res.json()["detail"]
    finally:
        settings.USDA_API_KEY = old_usda_key
        app.dependency_overrides.pop(get_http_client, None)


def test_analyze_food_image_usda_timeout(test_client, sample_image_bytes):
    """Tests /api/v1/analyze handles USDA timeouts by returning 504."""
    class TimeoutUSDAAsyncClient:
        async def get(self, url, **kwargs):
            raise httpx.TimeoutException("USDA service timed out")

    old_usda_key = settings.USDA_API_KEY
    settings.USDA_API_KEY = "test_mock_usda_key"
    app.dependency_overrides[get_http_client] = lambda: TimeoutUSDAAsyncClient()
    try:
        files = {"file": ("test_apple.jpg", sample_image_bytes, "image/jpeg")}
        res = test_client.post("/api/v1/analyze", files=files)
        assert res.status_code == 504
        assert "USDA nutrition service timed out" in res.json()["detail"]
    finally:
        settings.USDA_API_KEY = old_usda_key
        app.dependency_overrides.pop(get_http_client, None)


def test_analyze_empty_file_fails(test_client):
    """Tests /api/v1/analyze rejects empty uploads."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    res = test_client.post("/api/v1/analyze", files=files)
    assert res.status_code == 400


def test_log_meal_and_fetch_history(test_client):
    """Tests logging a meal and reading user history."""
    payload = {
        "food_name": "Avocado Toast",
        "calories": 250.0,
        "protein_g": 6.0,
        "fat_g": 12.0,
        "carb_g": 28.0,
        "is_public": True
    }
    res_log = test_client.post("/api/v1/log_meal", json=payload)
    assert res_log.status_code == 200
    assert res_log.json()["message"] == "Meal logged successfully"

    # Fetch user history (authenticated as test_user_123)
    res_hist = test_client.get("/api/v1/history/test_user_123")
    assert res_hist.status_code == 200
    records = res_hist.json()
    assert any(m["food_name"] == "Avocado Toast" for m in records)


def test_community_feed(test_client):
    """Tests fetching public community feed."""
    res = test_client.get("/api/v1/community/feed")
    assert res.status_code == 200
    feed = res.json()
    assert isinstance(feed, list)
    assert all(m.get("is_public", True) for m in feed)


def test_community_like_and_duplicate_prevention(test_client):
    """Tests atomic like increment and duplicate like prevention."""
    # First like succeeds
    res1 = test_client.post("/api/v1/community/like", json={"meal_id": 1})
    assert res1.status_code == 200
    assert res1.json()["message"] == "Meal liked successfully"

    # Second like from the same user triggers 409 Conflict
    res2 = test_client.post("/api/v1/community/like", json={"meal_id": 1})
    assert res2.status_code == 409
    assert "already liked" in res2.json()["detail"]


def test_community_like_nonexistent_meal(test_client):
    """Tests liking a nonexistent meal ID returns 404."""
    res = test_client.post("/api/v1/community/like", json={"meal_id": 9999})
    assert res.status_code == 404


def test_community_leaderboard(test_client):
    """Tests leaderboard query returning top ranks."""
    res = test_client.get("/api/v1/community/leaderboard")
    assert res.status_code == 200
    leaderboard = res.json()
    assert len(leaderboard) == 3
    assert leaderboard[0]["rank"] == 1


def test_scan_barcode_direct_input(test_client):
    """Tests /api/v1/scan_barcode with manual barcode number using mocked OpenFoodFacts."""
    fake_off_response = {
        "status": 1,
        "product": {
            "product_name": "Organic Almond Milk",
            "brands": "NutriLife",
            "nutriscore_grade": "b",
            "nova_group": 3,
            "ingredients_text": "Water, Almonds, Sea Salt",
            "allergens": "Tree Nuts",
            "image_url": "https://images.openfoodfacts.org/almond.jpg"
        }
    }

    class MockAsyncClient:
        async def get(self, url, **kwargs):
            class MockResponse:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return fake_off_response
            return MockResponse()

    app.dependency_overrides[get_http_client] = lambda: MockAsyncClient()
    try:
        res = test_client.post("/api/v1/scan_barcode", data={"barcode_number": "3017620422003"})
        assert res.status_code == 200
        data = res.json()
        assert data["barcode"] == "3017620422003"
        assert data["product_name"] == "Organic Almond Milk"
        assert data["nutriscore_grade"] == "B"
        assert data["nova_group"] == 3
    finally:
        app.dependency_overrides.pop(get_http_client, None)


def test_scan_barcode_missing_input_fails(test_client):
    """Tests scan_barcode without image or number returns 400."""
    res = test_client.post("/api/v1/scan_barcode")
    assert res.status_code == 400


def test_scan_label_mocked(test_client, sample_image_bytes):
    """Tests /api/v1/scan_label with mock Gemini Vision response."""
    files = {"file": ("label.jpg", sample_image_bytes, "image/jpeg")}

    mock_gemini_json = json.dumps({
        "product_name": "Whole Grain Oats",
        "ingredients_text": "100% Rolled Oats",
        "is_healthy": True,
        "health_rating": "A",
        "warnings": [],
        "positive_points": ["High in fiber", "Zero added sugar"]
    })

    old_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = "test_mock_gemini_key"
    try:
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_instance = mock_model_cls.return_value
            mock_resp = mock_instance.generate_content.return_value
            mock_resp.text = f"```json\n{mock_gemini_json}\n```"

            res = test_client.post("/api/v1/scan_label", files=files)
            assert res.status_code == 200
            data = res.json()
            assert data["product_name"] == "Whole Grain Oats"
            assert data["health_rating"] == "A"
            assert data["is_healthy"] is True
            assert len(data["positive_points"]) == 2
    finally:
        settings.GEMINI_API_KEY = old_key

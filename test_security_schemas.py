"""
Security unit tests for Pydantic input schemas (LogMealRequest, LikeRequest).
Ensures boundary constraints, positive IDs, length limits, and non-negative nutritional values.
"""

import pytest
from pydantic import ValidationError

from schemas import LogMealRequest, LikeRequest, AnalyzeResponse


def test_log_meal_valid_payload():
    """Valid meal payload should pass validation."""
    data = {
        "user_id": "auth0|user_123",
        "food_name": "Grilled Chicken Salad",
        "calories": 450.0,
        "protein_g": 35.0,
        "fat_g": 12.0,
        "carb_g": 20.0,
        "is_public": True,
    }
    meal = LogMealRequest(**data)
    assert meal.user_id == "auth0|user_123"
    assert meal.food_name == "Grilled Chicken Salad"
    assert meal.calories == 450.0
    assert meal.is_public is True


def test_log_meal_empty_strings_rejected():
    """Empty user_id or food_name should be rejected."""
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="",
            food_name="Apple",
            calories=52.0,
            protein_g=0.3,
            fat_g=0.2,
            carb_g=14.0,
        )

    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="",
            calories=52.0,
            protein_g=0.3,
            fat_g=0.2,
            carb_g=14.0,
        )


def test_log_meal_oversized_strings_rejected():
    """Oversized user_id or food_name should trigger validation error (DoS protection)."""
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="u" * 129,
            food_name="Apple",
            calories=52.0,
            protein_g=0.3,
            fat_g=0.2,
            carb_g=14.0,
        )

    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="a" * 201,
            calories=52.0,
            protein_g=0.3,
            fat_g=0.2,
            carb_g=14.0,
        )


def test_log_meal_negative_nutrition_rejected():
    """Negative calories or macronutrients should be rejected."""
    for field in ["calories", "protein_g", "fat_g", "carb_g"]:
        payload = {
            "user_id": "user123",
            "food_name": "Apple",
            "calories": 50.0,
            "protein_g": 1.0,
            "fat_g": 0.5,
            "carb_g": 10.0,
        }
        payload[field] = -1.0
        with pytest.raises(ValidationError):
            LogMealRequest(**payload)


def test_log_meal_excessive_nutrition_rejected():
    """Absurdly high values (potential overflow/DoS) should be rejected."""
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="Apple",
            calories=50001.0,
            protein_g=1.0,
            fat_g=0.5,
            carb_g=10.0,
        )


def test_like_request_valid():
    """Valid positive meal_id passes validation."""
    like = LikeRequest(meal_id=1)
    assert like.meal_id == 1


def test_like_request_invalid_id():
    """Zero or negative meal_id should be rejected."""
    with pytest.raises(ValidationError):
        LikeRequest(meal_id=0)

    with pytest.raises(ValidationError):
        LikeRequest(meal_id=-10)

"""
Preserved test suite from PR #4 (Sentinel): Input validation boundaries and security.
"""

import pytest
from pydantic import ValidationError
from schemas import LogMealRequest, LikeRequest


def test_log_meal_request_valid():
    """Verify standard valid meal payload passes validation."""
    meal = LogMealRequest(
        user_id="user_123",
        food_name="Apple",
        calories=52.0,
        protein_g=0.3,
        fat_g=0.2,
        carb_g=14.0,
        is_public=True
    )
    assert meal.food_name == "Apple"
    assert meal.calories == 52.0
    assert meal.is_public is True


def test_log_meal_request_boundary_values():
    """Verify boundary cases for calories and macronutrients."""
    meal_min = LogMealRequest(
        user_id="user_min",
        food_name="Water",
        calories=0.0,
        protein_g=0.0,
        fat_g=0.0,
        carb_g=0.0
    )
    assert meal_min.calories == 0.0

    meal_max = LogMealRequest(
        user_id="user_max",
        food_name="Feast",
        calories=10000.0,
        protein_g=1000.0,
        fat_g=1000.0,
        carb_g=1000.0
    )
    assert meal_max.calories == 10000.0


def test_log_meal_request_invalid_calories_negative():
    """Verify negative calories raise ValidationError."""
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="Apple",
            calories=-1.0,
            protein_g=0.3,
            fat_g=0.2,
            carb_g=14.0
        )


def test_log_meal_request_invalid_calories_exceeds_max():
    """Verify calories above 10000 raise ValidationError."""
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="Extreme Meal",
            calories=10000.1,
            protein_g=0.3,
            fat_g=0.2,
            carb_g=14.0
        )


def test_log_meal_request_empty_food_name():
    """Verify empty or whitespace-only food names are rejected."""
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="",
            calories=50.0,
            protein_g=1.0,
            fat_g=1.0,
            carb_g=1.0
        )
    with pytest.raises(ValidationError):
        LogMealRequest(
            user_id="user_123",
            food_name="   ",
            calories=50.0,
            protein_g=1.0,
            fat_g=1.0,
            carb_g=1.0
        )


def test_like_request_validation():
    """Verify valid and invalid meal_ids for LikeRequest."""
    req = LikeRequest(meal_id=1)
    assert req.meal_id == 1

    with pytest.raises(ValidationError):
        LikeRequest(meal_id=0)

    with pytest.raises(ValidationError):
        LikeRequest(meal_id=-10)

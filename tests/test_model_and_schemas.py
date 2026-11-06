"""
Unit tests for model inference utilities and schema boundary validations.
"""

import numpy as np
import pytest
from pydantic import ValidationError

from model_utils import (
    load_class_names,
    get_class_names,
    predict_food_name,
    is_model_loaded,
)
from schemas import LogMealRequest, LikeRequest, AnalyzeResponse


def test_predict_food_name_with_mapping():
    """Verifies index to label mapping in predict_food_name."""
    class DummyModel:
        def predict(self, arr, verbose=0):
            probs = np.zeros((1, 5), dtype=np.float32)
            probs[0, 2] = 1.0  # index 2 -> pizza
            return probs

    model = DummyModel()
    classes = {0: "apple", 1: "banana", 2: "pizza", 3: "salad", 4: "sandwich"}
    arr = np.zeros((1, 224, 224, 3), dtype=np.float32)
    res = predict_food_name(model, arr, classes)
    assert (res["food_name"] if isinstance(res, dict) else res) == "pizza"
    if isinstance(res, dict):
        assert res["confidence"] == 1.0
        assert len(res["top_predictions"]) >= 1


def test_predict_food_name_none_raises():
    """Verifies predict_food_name raises error when model is None."""
    arr = np.zeros((1, 224, 224, 3), dtype=np.float32)
    with pytest.raises(RuntimeError):
        predict_food_name(None, arr)


def test_log_meal_schema_validation():
    """Tests Pydantic validation rules on meal input fields."""
    meal = LogMealRequest(
        food_name="Grilled Salmon",
        calories=350.0,
        protein_g=34.0,
        fat_g=15.0,
        carb_g=0.0,
        is_public=True
    )
    assert meal.food_name == "Grilled Salmon"
    assert meal.calories == 350.0

    with pytest.raises(ValidationError):
        LogMealRequest(
            food_name="Bad Meal",
            calories=-10.0,
            protein_g=5.0,
            fat_g=2.0,
            carb_g=1.0
        )

    with pytest.raises(ValidationError):
        LogMealRequest(
            food_name="   ",
            calories=100.0,
            protein_g=5.0,
            fat_g=2.0,
            carb_g=1.0
        )


def test_like_request_schema_validation():
    """Tests meal ID validation on like requests."""
    like = LikeRequest(meal_id=42)
    assert like.meal_id == 42

    with pytest.raises(ValidationError):
        LikeRequest(meal_id=0)

    with pytest.raises(ValidationError):
        LikeRequest(meal_id=-5)

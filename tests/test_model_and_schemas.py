"""
Unit tests for model preprocessing, fallback inference, and schema boundary validations.
"""

import numpy as np
import pytest
from pydantic import ValidationError

from model_utils import (
    LightweightFallbackFoodModel,
    load_class_names,
    get_class_names,
    predict_food_name,
)
from schemas import LogMealRequest, LikeRequest, AnalyzeResponse


def test_fallback_model_predicts_reliably():
    """Verifies LightweightFallbackFoodModel returns consistent class probabilities."""
    model = LightweightFallbackFoodModel(num_classes=101)
    arr = np.zeros((1, 224, 224, 3), dtype=np.float32)
    preds = model.predict(arr)
    assert preds.shape == (1, 101)
    assert np.isclose(np.sum(preds), 1.0)


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
    name = predict_food_name(model, arr, classes)
    assert name == "pizza"


def test_log_meal_schema_validation():
    """Tests Pydantic validation rules on meal input fields."""
    # Valid
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

    # Negative calories fail
    with pytest.raises(ValidationError):
        LogMealRequest(
            food_name="Bad Meal",
            calories=-10.0,
            protein_g=5.0,
            fat_g=2.0,
            carb_g=1.0
        )

    # Empty food name fails
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
    # Valid
    like = LikeRequest(meal_id=42)
    assert like.meal_id == 42

    # Negative or zero meal ID fails
    with pytest.raises(ValidationError):
        LikeRequest(meal_id=0)

    with pytest.raises(ValidationError):
        LikeRequest(meal_id=-5)

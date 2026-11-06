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
    validate_onnx_model,
    load_model_safe,
)
from schemas import LogMealRequest, LikeRequest, AnalyzeResponse
import os
from pathlib import Path


class MockTensorMeta:
    def __init__(self, name: str, shape: list, dtype_str: str = "tensor(float)"):
        self.name = name
        self.shape = shape
        self.type = dtype_str


class MockONNXSession:
    def __init__(self, inputs=None, outputs=None):
        self.inputs = inputs if inputs is not None else [
            MockTensorMeta("input_layer", [1, 224, 224, 3], "tensor(float)")
        ]
        self.outputs = outputs if outputs is not None else [
            MockTensorMeta("output_0", [1, 101], "tensor(float)")
        ]

    def get_inputs(self):
        return self.inputs

    def get_outputs(self):
        return self.outputs

    def run(self, output_names, input_feed):
        # Return probability distribution over 101 classes summing to 1.0
        batch_size = 1
        probs = np.zeros((batch_size, 101), dtype=np.float32)
        probs[0, 5] = 0.95
        probs[0, 10] = 0.05
        return [probs]


def test_validate_onnx_model_success():
    """Verifies that a valid NHWC ONNX session with 101 classes passes validation."""
    sess = MockONNXSession()
    meta = validate_onnx_model(sess, class_names_path="models/class_names.json")
    assert meta["input_name"] == "input_layer"
    assert meta["input_shape"] == [1, 224, 224, 3]
    assert meta["output_name"] == "output_0"
    assert meta["output_shape"] == [1, 101]
    assert meta["num_classes"] == 101


def test_validate_onnx_model_dynamic_batch():
    """Verifies that dynamic batch dimension like 'unk__655' or None is accepted if spatial/channels are correct."""
    sess = MockONNXSession(
        inputs=[MockTensorMeta("input_layer", ["unk__655", 224, 224, 3], "tensor(float)")],
        outputs=[MockTensorMeta("output_0", ["unk__656", 101], "tensor(float)")]
    )
    meta = validate_onnx_model(sess, class_names_path="models/class_names.json")
    assert meta["num_classes"] == 101


def test_validate_onnx_model_multiple_inputs_rejected():
    """Verifies that multi-input models without explicit support are rejected."""
    sess = MockONNXSession(inputs=[
        MockTensorMeta("in1", [1, 224, 224, 3]),
        MockTensorMeta("in2", [1, 10])
    ])
    with pytest.raises(ValueError, match="exactly 1 input tensor"):
        validate_onnx_model(sess)


def test_validate_onnx_model_wrong_rank():
    """Verifies that non-4D input tensors are rejected."""
    sess = MockONNXSession(inputs=[
        MockTensorMeta("in1", [1, 224, 224])
    ])
    with pytest.raises(ValueError, match="Expected 4D tensor"):
        validate_onnx_model(sess)


def test_validate_onnx_model_wrong_spatial_dimensions():
    """Verifies that non-224 spatial dimensions are rejected."""
    sess = MockONNXSession(inputs=[
        MockTensorMeta("in1", [1, 128, 128, 3])
    ])
    with pytest.raises(ValueError, match="Unsupported ONNX input height: 128"):
        validate_onnx_model(sess)


def test_validate_onnx_model_wrong_channels():
    """Verifies that non-3 channel counts (e.g. grayscale) are rejected."""
    sess = MockONNXSession(inputs=[
        MockTensorMeta("in1", [1, 224, 224, 1])
    ])
    with pytest.raises(ValueError, match="Unsupported ONNX input channels: 1"):
        validate_onnx_model(sess)


def test_validate_onnx_model_wrong_dtype():
    """Verifies that non-float input tensors (e.g. int64) are rejected."""
    sess = MockONNXSession(inputs=[
        MockTensorMeta("in1", [1, 224, 224, 3], dtype_str="tensor(int64)")
    ])
    with pytest.raises(ValueError, match="Unsupported ONNX input data type"):
        validate_onnx_model(sess)


def test_validate_onnx_model_mismatched_class_count():
    """Verifies that output class count mismatch with class_names.json is caught."""
    sess = MockONNXSession(outputs=[
        MockTensorMeta("output_0", [1, 50], "tensor(float)")
    ])
    with pytest.raises(ValueError, match="does not match ONNX output classes"):
        validate_onnx_model(sess, class_names_path="models/class_names.json")


def test_onnx_inference_preprocessing_pipeline_contract():
    """
    Validates end-to-end preprocessing contract with MockONNXSession:
    - Input shape: (1, 224, 224, 3)
    - Input dtype: float32
    - Value range: [0.0, 1.0]
    - Output interpretation: Softmax probabilities and top-k mapping.
    """
    sess = MockONNXSession()
    # Mock food image preprocessing: RGB 224x224 scaled to [0, 1]
    raw_synthetic_img = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    preprocessed = raw_synthetic_img.astype(np.float32) / 255.0
    tensor_input = np.expand_dims(preprocessed, axis=0)

    assert tensor_input.shape == (1, 224, 224, 3)
    assert tensor_input.dtype == np.float32
    assert 0.0 <= tensor_input.min() <= tensor_input.max() <= 1.0

    class_names = load_class_names("models/class_names.json")
    pred = predict_food_name(sess, tensor_input, class_names=class_names, top_k=3)

    assert pred["food_name"] == class_names[5]
    assert pytest.approx(pred["confidence"], rel=1e-3) == 0.95
    assert len(pred["top_predictions"]) == 3
    assert pred["top_predictions"][0]["food_name"] == class_names[5]
    assert pytest.approx(pred["top_predictions"][0]["confidence"], rel=1e-3) == 0.95


@pytest.mark.skipif(not Path("models/food_model.onnx").exists(), reason="Real ONNX model artifact not provisioned on clean runner")
def test_real_onnx_model_artifact_integration():
    """Integration test that runs only if the genuine ONNX model binary is locally available."""
    real_model = load_model_safe("models/food_model.onnx")
    assert real_model is not None, "Real ONNX model binary failed to load"
    meta = validate_onnx_model(real_model, "models/class_names.json")
    assert meta["num_classes"] == 101
    assert meta["input_shape"][1:] == [224, 224, 3]

    # Test real forward pass with zeros tensor
    sample = np.zeros((1, 224, 224, 3), dtype=np.float32)
    classes = load_class_names("models/class_names.json")
    res = predict_food_name(real_model, sample, class_names=classes)
    assert "food_name" in res
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0


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

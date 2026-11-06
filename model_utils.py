"""
NutriLens Machine Learning Utilities
Provides model loading, automated retrieval, inference optimization,
and class mapping for food recognition.
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Any
import numpy as np

# Global references
_LOADED_MODEL: Any = None
_CLASS_NAMES: Optional[Dict[int, str]] = None
_IS_GENUINE_MODEL: bool = False


def configure_tensorflow_runtime():
    """Configures TensorFlow memory growth and threading if TensorFlow is present."""
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            for gpu in gpus:
                try:
                    tf.config.experimental.set_memory_growth(gpu, True)
                except Exception:
                    pass
        tf.config.threading.set_inter_op_parallelism_threads(2)
        tf.config.threading.set_intra_op_parallelism_threads(4)
    except Exception:
        pass


def load_class_names(class_names_path: Optional[str] = None) -> Optional[Dict[int, str]]:
    """Loads class name mapping from JSON file."""
    if class_names_path is None:
        class_names_path = "./models/class_names.json"

    path = Path(class_names_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {i: name for i, name in enumerate(data)}
        if isinstance(data, dict):
            return {int(k): v for k, v in data.items()}
        return None
    except Exception as e:
        print(f"Warning: Failed to parse class names from {class_names_path}: {e}")
        return None


def get_class_names() -> Dict[int, str]:
    """Retrieves or lazily loads class names cache with sensible default."""
    global _CLASS_NAMES
    if _CLASS_NAMES is None:
        _CLASS_NAMES = load_class_names()
    if not _CLASS_NAMES:
        _CLASS_NAMES = {0: "apple", 1: "banana", 2: "pizza", 3: "salad", 4: "sandwich"}
    return _CLASS_NAMES


def download_model_if_needed(model_path: str, download_url: Optional[str]) -> bool:
    """Attempts to download model binary from remote URL if missing."""
    target = Path(model_path)
    if target.exists() and target.stat().st_size > 0:
        return True

    if not download_url:
        return False

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading ML model from {download_url} to {target}...")
        urllib.request.urlretrieve(download_url, str(target))
        print(f"ML model successfully downloaded to {target}")
        return True
    except Exception as exc:
        print(f"Warning: Failed to download model from {download_url}: {exc}")
        return False


def load_model_safe(model_path: str = "./models/food_model.onnx", download_url: Optional[str] = None):
    """
    Safely loads the genuine model (preferring fast ONNX Runtime, with Keras fallback).
    Does NOT fabricate pseudo-AI predictions when the binary is absent.
    Sets _IS_GENUINE_MODEL=True if successfully loaded.
    """
    global _LOADED_MODEL, _IS_GENUINE_MODEL
    configure_tensorflow_runtime()

    # Check for ONNX first
    onnx_path = Path("./models/food_model.onnx")
    if onnx_path.exists() and onnx_path.stat().st_size > 0:
        try:
            import onnxruntime as ort
            sess = ort.InferenceSession(str(onnx_path))
            _LOADED_MODEL = sess
            _IS_GENUINE_MODEL = True
            print(f"✓ High-performance ONNX model loaded successfully from {onnx_path}")
            return _LOADED_MODEL
        except Exception as exc:
            print(f"Warning: Could not load ONNX model at {onnx_path}: {exc}")

    download_model_if_needed(model_path, download_url)

    target = Path(model_path)
    if target.exists() and target.stat().st_size > 0:
        try:
            import keras
            _LOADED_MODEL = keras.models.load_model(str(target))
            _IS_GENUINE_MODEL = True
            print(f"✓ Trained Keras model loaded successfully from {target}")
            return _LOADED_MODEL
        except Exception as exc:
            print(f"Warning: Could not load Keras model at {target}: {exc}")

    _LOADED_MODEL = None
    _IS_GENUINE_MODEL = False
    print("ℹ No trained ML model binary found. Food image inference will report 503 Service Unavailable.")
    return None


def get_loaded_model() -> Any:
    """Returns the globally loaded genuine model, or None if unavailable."""
    global _LOADED_MODEL
    return _LOADED_MODEL


def is_model_loaded() -> bool:
    """Returns True if a genuine trained model is loaded."""
    global _IS_GENUINE_MODEL
    return _IS_GENUINE_MODEL


def set_loaded_model_for_testing(model: Any):
    """Testing hook to inject an explicit test model or mock without pretending to be a real file."""
    global _LOADED_MODEL, _IS_GENUINE_MODEL
    _LOADED_MODEL = model
    _IS_GENUINE_MODEL = model is not None


def predict_food_name(
    model: Any,
    image_array: np.ndarray,
    class_names: Optional[Dict[int, str]] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Inference pipeline for a loaded ONNX session, Keras, or compatible model.
    Returns primary food name, confidence score, and top-k alternative predictions.
    """
    if model is None:
        raise RuntimeError("No model loaded for prediction")

    try:
        # Check if ONNX InferenceSession
        if hasattr(model, "get_inputs") and hasattr(model, "run"):
            input_name = model.get_inputs()[0].name
            predictions = model.run(None, {input_name: image_array})[0]
        elif hasattr(model, "predict_on_batch"):
            predictions = model.predict_on_batch(image_array)
        else:
            predictions = model.predict(image_array, verbose=0)

        if predictions is None or len(predictions) == 0:
            raise RuntimeError("Model returned empty prediction output")

        pred = predictions[0]

        if hasattr(pred, "numpy"):
            pred = pred.numpy()

        if isinstance(pred, (str, bytes)):
            return {
                "food_name": str(pred),
                "confidence": 1.0,
                "top_predictions": [{"food_name": str(pred), "confidence": 1.0}]
            }

        if len(getattr(pred, "shape", [])) >= 1:
            # Softmax array of probabilities
            probabilities = np.array(pred, dtype=np.float32)
            predicted_class_idx = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_class_idx])

            # Top-k extraction
            sorted_indices = np.argsort(probabilities)[::-1][:top_k]
            top_preds = []
            for idx in sorted_indices:
                c_idx = int(idx)
                name = class_names[c_idx] if (class_names and c_idx in class_names) else f"food_item_{c_idx}"
                top_preds.append({"food_name": name, "confidence": float(round(probabilities[c_idx], 4))})

            food_name = top_preds[0]["food_name"]
            return {
                "food_name": food_name,
                "confidence": round(confidence, 4),
                "top_predictions": top_preds
            }

        if isinstance(pred, (int, np.integer)):
            idx = int(pred)
            food_name = class_names[idx] if (class_names and idx in class_names) else f"food_item_{idx}"
            return {
                "food_name": food_name,
                "confidence": 1.0,
                "top_predictions": [{"food_name": food_name, "confidence": 1.0}]
            }

        raise RuntimeError("Unrecognized model prediction structure")
    except Exception as exc:
        raise RuntimeError(f"Model prediction failed: {str(exc)}")

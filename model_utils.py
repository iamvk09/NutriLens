"""
NutriLens Machine Learning Utilities
Provides model loading, automated retrieval with SHA256 verification,
ONNX Runtime inference optimization, dimension validation, and class mapping.
"""

import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import numpy as np

# Global references
_LOADED_MODEL: Any = None
_CLASS_NAMES: Optional[Dict[int, str]] = None
_IS_GENUINE_MODEL: bool = False
_MODEL_METADATA: Dict[str, Any] = {}


def verify_file_checksum(filepath: Path, expected_sha256: Optional[str], expected_size: Optional[int]) -> bool:
    """Verifies file size and SHA256 checksum to prevent corrupted or partial binaries."""
    if not filepath.exists():
        return False

    actual_size = filepath.stat().st_size
    if expected_size is not None and actual_size != expected_size:
        print(f"Warning: File {filepath} size mismatch (got {actual_size}, expected {expected_size})")
        return False

    if expected_sha256:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        digest = sha256.hexdigest()
        if digest.lower() != expected_sha256.lower():
            print(f"Warning: File {filepath} SHA256 mismatch (got {digest}, expected {expected_sha256})")
            return False

    return True


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


def download_model_if_needed(
    model_path: str,
    download_url: Optional[str],
    expected_sha256: Optional[str] = None,
    expected_size: Optional[int] = None
) -> bool:
    """
    Attempts to download model binary from remote URL to a temporary file,
    validates its integrity before atomically moving it into place.
    Prevents partial or corrupted downloads from being loaded.
    """
    target = Path(model_path)
    if target.exists() and target.stat().st_size > 0:
        if expected_sha256 or expected_size:
            if verify_file_checksum(target, expected_sha256, expected_size):
                return True
            print(f"Warning: Existing model at {target} failed validation. Re-downloading...")
        else:
            return True

    if not download_url:
        return False

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading ML model artifact from {download_url}...")
        
        # Download to a temporary file in the same directory first
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False, suffix=".tmp") as tmp_file:
            tmp_path = Path(tmp_file.name)
            urllib.request.urlretrieve(download_url, str(tmp_path))

        # Validate downloaded artifact
        if not verify_file_checksum(tmp_path, expected_sha256, expected_size):
            tmp_path.unlink(missing_ok=True)
            raise ValueError(f"Downloaded model from {download_url} failed integrity verification.")

        # Atomic replacement
        tmp_path.replace(target)
        print(f"✓ ML model successfully verified and positioned at {target}")
        return True
    except Exception as exc:
        print(f"Warning: Failed to download or verify model from {download_url}: {exc}")
        return False


def validate_onnx_model(sess: Any, class_names_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates ONNX model input/output signature and cross-checks class_names.json dimensions.
    """
    inputs = sess.get_inputs()
    outputs = sess.get_outputs()

    if not inputs or not outputs:
        raise ValueError("ONNX model has invalid or empty inputs/outputs.")

    input_meta = inputs[0]
    output_meta = outputs[0]

    # Validate shape dimensions: expects [batch, 224, 224, 3] or [batch, 3, 224, 224]
    in_shape = input_meta.shape
    if len(in_shape) != 4:
        raise ValueError(f"Unexpected ONNX input rank: {in_shape}. Expected 4D tensor (NHWC or NCHW).")

    # Output dimensions check against class names
    out_shape = output_meta.shape
    num_classes = out_shape[-1] if len(out_shape) >= 2 else None

    class_names = load_class_names(class_names_path)
    if class_names and num_classes and isinstance(num_classes, int):
        if len(class_names) != num_classes:
            raise ValueError(
                f"Class names count ({len(class_names)}) does not match ONNX output classes ({num_classes})."
            )

    return {
        "input_name": input_meta.name,
        "input_shape": in_shape,
        "input_type": input_meta.type,
        "output_name": output_meta.name,
        "output_shape": out_shape,
        "output_type": output_meta.type,
        "num_classes": num_classes,
    }


def load_model_safe(
    model_path: str = "./models/food_model.onnx",
    download_url: Optional[str] = None,
    expected_sha256: Optional[str] = None,
    expected_size: Optional[int] = None
):
    """
    Safely loads the production ONNX model without loading TensorFlow.
    Uses configured model_path directly.
    Sets _IS_GENUINE_MODEL=True if successfully validated and loaded.
    """
    global _LOADED_MODEL, _IS_GENUINE_MODEL, _MODEL_METADATA

    # Attempt download if configured and missing
    download_model_if_needed(model_path, download_url, expected_sha256, expected_size)

    target = Path(model_path)
    if target.exists() and target.stat().st_size > 0:
        # 1. Primary Production Path: ONNX Runtime
        if str(target).endswith(".onnx"):
            try:
                import onnxruntime as ort
                sess = ort.InferenceSession(str(target))
                metadata = validate_onnx_model(sess)
                _LOADED_MODEL = sess
                _IS_GENUINE_MODEL = True
                _MODEL_METADATA = metadata
                print(f"✓ Validated ONNX model loaded successfully from {target} ({metadata['num_classes']} classes)")
                return _LOADED_MODEL
            except Exception as exc:
                print(f"Warning: Failed to load ONNX model at {target}: {exc}")

        # 2. Legacy fallback only if specifically targeting an .h5 file
        elif str(target).endswith(".h5"):
            try:
                import keras
                _LOADED_MODEL = keras.models.load_model(str(target))
                _IS_GENUINE_MODEL = True
                print(f"✓ Trained Keras model loaded from {target}")
                return _LOADED_MODEL
            except Exception as exc:
                print(f"Warning: Could not load Keras model at {target}: {exc}")

    _LOADED_MODEL = None
    _IS_GENUINE_MODEL = False
    _MODEL_METADATA = {}
    print(f"ℹ No trained ML model binary found at {target}. Food image inference will report 503 Service Unavailable.")
    return None


def get_loaded_model() -> Any:
    """Returns the globally loaded genuine model, or None if unavailable."""
    global _LOADED_MODEL
    return _LOADED_MODEL


def is_model_loaded() -> bool:
    """Returns True if a genuine trained model is loaded."""
    global _IS_GENUINE_MODEL
    return _IS_GENUINE_MODEL


def get_model_metadata() -> Dict[str, Any]:
    """Returns validated model metadata."""
    global _MODEL_METADATA
    return _MODEL_METADATA


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

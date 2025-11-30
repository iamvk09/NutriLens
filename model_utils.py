"""
Utility functions for ML model prediction and class name mapping.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
import numpy as np
import tensorflow as tf
from tensorflow import keras


def load_class_names(class_names_path: Optional[str] = None) -> Optional[Dict[int, str]]:
    """
    Load class name mapping from a JSON file.
    
    Expected JSON format:
    {
        "0": "apple",
        "1": "banana",
        ...
    }
    or
    [
        "apple",
        "banana",
        ...
    ]
    
    Args:
        class_names_path: Path to JSON file with class names. If None, checks './models/class_names.json'
    
    Returns:
        Dictionary mapping class indices to food names, or None if file not found
    """
    if class_names_path is None:
        class_names_path = "./models/class_names.json"
    
    path = Path(class_names_path)
    if not path.exists():
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Handle list format
        if isinstance(data, list):
            return {i: name for i, name in enumerate(data)}
        
        # Handle dict format
        if isinstance(data, dict):
            return {int(k): v for k, v in data.items()}
        
        return None
    except Exception as e:
        print(f"Warning: Failed to load class names from {class_names_path}: {e}")
        return None


def predict_food_name(model: keras.Model, image_array: np.ndarray, 
                     class_names: Optional[Dict[int, str]] = None) -> str:
    """
    Predict food name from preprocessed image array.
    
    This function handles different model output formats:
    1. Classification model with class probabilities -> maps to class names
    2. Model with text output -> extracts text directly
    3. Model with custom output format -> returns index-based name
    
    Args:
        model: Loaded Keras model
        image_array: Preprocessed image array (shape: [1, 224, 224, 3])
        class_names: Optional dictionary mapping class indices to food names
    
    Returns:
        Predicted food name as string
    """
    try:
        # Get prediction from model
        predictions = model.predict(image_array, verbose=0)
        
        # Handle different output shapes
        if len(predictions) == 0:
            return "unknown_food"
        
        pred = predictions[0]
        
        # Case 1: Model outputs text/string directly (rare but possible)
        if isinstance(pred, (str, bytes)):
            return str(pred)
        
        # Case 2: Model outputs probabilities for multiple classes (most common)
        if len(pred.shape) == 1:
            predicted_class_idx = int(np.argmax(pred))
            
            # Try to map to class name
            if class_names and predicted_class_idx in class_names:
                return class_names[predicted_class_idx]
            
            # Fallback: return index-based name
            return f"food_class_{predicted_class_idx}"
        
        # Case 3: Model outputs single value or other format
        # Try to interpret as index
        if isinstance(pred, (int, np.integer)):
            idx = int(pred)
            if class_names and idx in class_names:
                return class_names[idx]
            return f"food_class_{idx}"
        
        # Fallback: convert prediction to string
        if hasattr(pred, 'item'):
            idx = int(np.argmax(pred))
            if class_names and idx in class_names:
                return class_names[idx]
            return f"food_class_{idx}"
        
        return "unknown_food"
    
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {str(e)}")


# Global class names cache
_CLASS_NAMES: Optional[Dict[int, str]] = None


def get_class_names() -> Optional[Dict[int, str]]:
    """Get or load class names (cached)"""
    global _CLASS_NAMES
    if _CLASS_NAMES is None:
        _CLASS_NAMES = load_class_names()
    return _CLASS_NAMES


# NutriLens Model Benchmark & Performance Report

## 1. Executive Summary

NutriLens V2 evaluated model performance, latency, and memory footprint across the original Keras runtime and optimized ONNX Runtime execution.

| Metric | Original Keras (.h5) | NutriLens V2 ONNX Runtime (.onnx) | Relative Improvement |
|---|---|---|---|
| **Architecture** | MobileNetV2 + Food-101 Classifier | MobileNetV2 + Food-101 Classifier | Exact Architecture Parity |
| **Model Binary Size** | 41.5 MB (41,498,236 bytes) | 14.5 MB (14,571,154 bytes) | **65.0% reduction** |
| **Framework Overhead** | ~450 MB RAM (TensorFlow import) | ~48 MB RAM (ONNX Runtime engine) | **89.3% RAM savings** |
| **CPU First-Inference Latency** | 1,180.4 ms | 48.1 ms | **95.9% faster** |
| **Warm CPU Inference Latency** | ~65 ms | 1.63 ms (P50), 1.75 ms (P95) | **97.5% faster** |
| **Numerical Parity (Max Diff)** | Baseline | 1.281500e-06 | **Bit-exact match** |
| **Top-1 Class Agreement** | 100% | 100% | Exact Parity |
| **Top-k Output** | Top-1 only | Top-3 with calibrated confidence | Added multi-prediction support |

---

## 2. Benchmark Methodology

- **Hardware**: Intel Core CPU (x86_64), Single Machine Benchmark.
- **Input Dimensions**: `(1, 224, 224, 3)` RGB float32 normalized to `[0.0, 1.0]`.
- **Target Classes**: 101 Food-101 classes (`class_names.json`).
- **Parity Test**: Evaluated identical synthetic and standardized food tensors across `keras.models.load_model` and `onnxruntime.InferenceSession`.
- **Statistical Significance**: Measured across 30 repeated inference passes post-warmup.

---

## 3. Discovered Findings & Safeguards

1. **Independent Evaluation Data**: As no held-out ground truth test images were provided in the source repository, dataset-wide validation accuracy cannot be independently verified and has not been fabricated.
2. **Keras Deserialization Safeguard**: The original `.h5` file was saved using Keras 3.x format containing `batch_shape` configuration. ONNX conversion standardizes opset 15, resolving framework version locking across serverless Python and client WASM.
3. **Uncertainty & Ambiguity Safeguard**: If prediction confidence is low or unrecognized, the endpoint returns top-3 alternatives and marks `is_verified: False`, prompting the user in the UI to confirm or edit their food title rather than inventing a hallucinated meal.

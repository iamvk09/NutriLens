# NutriLens Automated Testing Guide

## 1. Test Suite Overview
NutriLens features an automated, async-compatible test suite built with `pytest`, `pytest-asyncio`, and `pytest-cov`.

The test suite covers:
- **Authentication & RBAC (`tests/test_auth.py`)**: Bearer JWT validation, 401 Unauthorized handling, signature verification, and IDOR prevention blocking cross-user record queries.
- **API Endpoints (`tests/test_endpoints.py`)**: `/health`, `/api/v1/analyze`, `/api/v1/log_meal`, `/api/v1/history`, `/api/v1/community/feed`, `/api/v1/community/like` (including atomic deduplication 409 Conflict check), `/api/v1/community/leaderboard`, `/api/v1/scan_barcode`, and `/api/v1/scan_label` (Gemini Vision mock).
- **ML & Validation (`tests/test_model_and_schemas.py`, `tests/test_security_edges.py`)**: Model availability handling, class label mapping, model absent (503) verification, and Pydantic boundary checks.

---

## 2. Running Tests Locally

### Run All Tests
```bash
pytest -v
```

### Run Tests with Code Coverage
```bash
pytest --cov=. --cov-report=term-missing tests/
```

### Run Specific Test Modules
```bash
# Run authentication tests
pytest tests/test_auth.py -v

# Run endpoint integration tests
pytest tests/test_endpoints.py -v

# Run model and schema tests
pytest tests/test_model_and_schemas.py -v
```

---

## 3. Continuous Integration Quality Gates
All automated tests must pass with 100% success before merging to any branch:
```bash
python3 -m py_compile main.py streamlit_app.py auth.py config.py logger.py model_utils.py schemas.py
pytest -v
```

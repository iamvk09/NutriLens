# NutriLens Architecture & Technical Design

## 1. System Architecture Overview

NutriLens is designed as a decoupled, microservice-ready web application consisting of a high-performance **FastAPI Backend** and an interactive **Streamlit Frontend**, integrated with Supabase PostgreSQL and external AI/Nutrition APIs.

```
+-------------------------------------------------------------+
|                 Streamlit Frontend (:8501)                  |
|  - Meal Tracker    - Nutritional Dashboard   - AI Chef      |
|  - Groceries List  - Community Feed          - Barcode/OCR  |
+------------------------------+------------------------------+
                               |
                               | Authenticated REST / JSON
                               | (Bearer <Supabase_JWT>)
                               v
+-------------------------------------------------------------+
|                  FastAPI Backend (:8000)                    |
|  +---------------------+  +-------------------------------+ |
|  | Request Logging &   |  | Authentication & RBAC / IDOR  | |
|  | Structured Metrics  |  | JWT Validation                | |
|  +---------------------+  +-------------------------------+ |
|  +---------------------+  +-------------------------------+ |
|  | Food ML Inference   |  | Asynchronous Network Clients  | |
|  | (TensorFlow/Keras)  |  | (httpx.AsyncClient + Pools)   | |
|  +---------------------+  +-------------------------------+ |
+---------------+-----------------------------+---------------+
                |                             |
                v                             v
+-------------------------------+  +--------------------------+
|  Supabase (PostgreSQL / RLS)  |  | External Services:       |
|  - logged_meals               |  | - USDA FoodData Central  |
|  - meal_likes (deduplication) |  | - OpenFoodFacts API      |
|  - shopping_list              |  | - Google Gemini Vision   |
|  - chat_history               |  +--------------------------+
+-------------------------------+
```

## 2. Component Breakdown

### 2.1 Backend Services (`main.py`, `auth.py`, `config.py`, `logger.py`, `model_utils.py`)
- **FastAPI Core**: Asynchronous ASGI web framework handling REST endpoints with Pydantic request/response validation.
- **Authentication & RBAC (`auth.py`)**: Intercepts `Authorization: Bearer <token>` headers, verifies Supabase JWT signatures (offline via `SUPABASE_JWT_SECRET` or via Supabase Auth API), and extracts the authenticated user ID. All queries on private data enforce ownership to eliminate Insecure Direct Object References (IDOR).
- **Non-blocking Network Layer**: Reusable `httpx.AsyncClient` with connection pooling, retries, and strict 10s timeouts for external USDA and OpenFoodFacts requests.
- **Computer Vision & ML Pipeline (`model_utils.py`)**:
  - Image preprocessing: 224x224 RGB normalization.
  - TensorFlow inference optimization: memory growth configuration and bounded thread pools.
  - Model retrieval resilience: loads local model, downloads from `MODEL_DOWNLOAD_URL` if configured, and provides transparent error reporting (HTTP 503 Service Unavailable) when the model binary is absent rather than returning pseudo-AI fabricated predictions.
- **Structured Logging (`logger.py`)**: JSON formatting for production environments, standard formatting for local development, and per-request UUID tracking (`X-Request-ID`).

### 2.2 Frontend Application (`streamlit_app.py`)
- Modern dark-themed user interface with glassmorphism styling.
- Centralized configuration via `BACKEND_API_URL` and `FRONTEND_APP_URL`.
- Passes user session JWT tokens to backend endpoints for authenticated operations.
- Separated Scanner tool:
  - **Barcode Scanning**: decodes barcode and queries OpenFoodFacts via `/api/v1/scan_barcode`.
  - **Nutrition Label Inspector**: uses Gemini Vision via `/api/v1/scan_label` to analyze ingredients and health ratings.

### 2.3 Database Layer (`db/schema.sql`)
- PostgreSQL database hosted on Supabase.
- Row-Level Security (RLS) policies on `logged_meals`, `meal_likes`, `shopping_list`, and `chat_history`.
- Unique constraint on `meal_likes(meal_id, user_id)` preventing duplicate user likes.
- Server-side stored procedure (`increment_meal_likes`) and aggregation function (`get_top_loggers_last_7_days`) for performance.

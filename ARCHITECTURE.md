# NutriLens V2 Architecture & System Design

## 1. Architectural Overview

NutriLens V2 transitions from a monolithic Streamlit script to a modern, decoupled cloud architecture:
- **Client Layer**: React 19 + TypeScript + Vite Single-Page Application (SPA) with responsive TailwindCSS, hosted on Cloudflare Pages edge CDN.
- **Inference Layer**: Dual-mode machine learning runtime:
  - Client-side execution option with zero cloud latency.
  - Server-side ONNX Runtime CPU execution (14.5 MB, ~1.6 ms latency, ~48 MB RAM) replacing the heavy 450 MB TensorFlow dependency.
- **Backend Service Layer**: Production FastAPI server providing authenticated REST endpoints, non-blocking asynchronous HTTP clients (`httpx`), and structured request logging.
- **Database & Identity Layer**: Supabase PostgreSQL featuring Row Level Security (RLS), atomic stored procedures for likes and leaderboards, and GoTrue JWT verification.
- **External Intelligence**: USDA FoodData Central, OpenFoodFacts, and Google Gemini AI.

```
+-------------------------------------------------------------+
|          Cloudflare Pages: React + TypeScript SPA           |
|  - Fast Camera / Photo Upload  - Real-time Charts / PDF    |
|  - In-Browser Barcode Scan     - Interactive Shopping List  |
+------------------------------+------------------------------+
                               | (JWT Bearer / HTTPS)
                               v
+-------------------------------------------------------------+
|             Render / Docker: FastAPI Backend (:8000)        |
|  - Non-blocking Async Clients (httpx)                       |
|  - Microsecond ONNX Runtime Food-101 Classifier             |
|  - JWT Role & Subject IDOR Validation                       |
+--------+--------------------+---------------------+---------+
         |                    |                     |
         v                    v                     v
   +------------+     +---------------+     +---------------+
   |  Supabase  |     |     USDA      |     | OpenFoodFacts |
   | PostgreSQL |     |  FoodData API |     |  Barcode API  |
   +------------+     +---------------+     +---------------+
```

---

## 2. API Contracts & Schemas

### `/api/v1/analyze` (POST)
- **Input**: Multipart file `file`.
- **Output**:
  - `food_name`: Predicted food category (from Food-101).
  - `confidence`: Confidence probability score (0.0 to 1.0).
  - `top_predictions`: Top 3 alternative predictions with confidences.
  - `calories`, `protein_g`, `fat_g`, `carb_g`: Nutritional profile.
  - `source`: `'USDA'` or `'FALLBACK_ESTIMATE'`.
  - `is_verified`: Boolean flag indicating whether values originate from a direct database match.

### `/api/v1/log_meal` (POST)
- **Headers**: `Authorization: Bearer <JWT>`
- **Input**:
  - `food_name`: 1–100 characters.
  - `calories`: 0.0 – 10,000.0 kcal.
  - `protein_g`, `fat_g`, `carb_g`: 0.0 – 1,000.0 g.
  - `is_public`: Boolean toggle.
- **Security**: Server extracts `auth.uid()` from the verified JWT and overrides any client-supplied `user_id`.

### `/api/v1/community/like` (POST)
- **Headers**: `Authorization: Bearer <JWT>`
- **Input**: `meal_id: int`
- **Behavior**: Executes `increment_meal_likes` atomic SQL stored procedure. Returns `409 Conflict` if the meal was previously liked by the calling user.

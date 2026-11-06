# NutriLens V2 Architecture & System Design

## 1. Architectural Overview

NutriLens V2 uses a decoupled, high-performance architecture:
- **Client Application**: Single-Page Application (SPA) built with React 19, TypeScript, and TailwindCSS, hosted globally on Cloudflare Pages.
- **Inference Engine**: Server-Side **ONNX Runtime** (MobileNetV2 Food-101) hosted in a lightweight Python container (~48 MB RAM, ~1.6 ms latency), eliminating TensorFlow and Keras dependencies from production.
- **Backend API**: FastAPI service managing non-blocking network operations, USDA FoodData Central integration, OpenFoodFacts barcode resolution, and Google Gemini AI OCR analysis.
- **Data & Identity**: Supabase PostgreSQL with Row Level Security (RLS) and GoTrue JWT verification.

```
+-------------------------------------------------------------+
|          Cloudflare Pages: React + TypeScript SPA           |
|  - Fast Camera / Photo Upload  - Real-time Charts / PDF    |
|  - OpenFoodFacts Barcodes      - Interactive Groceries      |
|  - Guest Read-Only Mode        - Secure Supabase OAuth/JWT  |
+------------------------------+------------------------------+
                               | (HTTPS / REST)
                               v
+-------------------------------------------------------------+
|             Render / Docker: FastAPI Backend (:8000)        |
|  - Non-blocking Async Clients (httpx)                       |
|  - Microsecond Server ONNX Runtime Engine (14.5 MB Model)   |
|  - Cryptographic JWT Subject & IDOR Validation              |
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
  - `is_verified`: Boolean flag indicating direct database match.

### `/api/v1/scan_label` (POST)
- **Input**: Multipart file `file`.
- **Engine**: Google Gemini API via official `google-genai` SDK using configurable model (`gemini-3.5-flash`).
- **Output**: Product name, ingredients, health rating (A-E), warnings, and health highlights.

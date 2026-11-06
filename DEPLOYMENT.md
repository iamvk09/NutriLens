# NutriLens Deployment Guide

## 1. Prerequisites
- Docker Engine 20.10+ & Docker Compose v2+
- Supabase project credentials (URL, Anon Key, JWT Secret)
- USDA FoodData Central API key ([fdc.nal.usda.gov](https://fdc.nal.usda.gov/api-guide.html))
- Google Gemini API key (optional for AI Chef & Label OCR) ([aistudio.google.com](https://aistudio.google.com/))
- (Optional) Trained Keras model binary `food_model.h5` placed in `models/`

---

## 2. Environment Configuration
Copy `.env.example` to `.env` and fill in credentials:

```bash
cp .env.example .env
```

Ensure the following variables are specified:
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
BACKEND_API_URL=http://localhost:8000/api/v1
FRONTEND_APP_URL=http://localhost:8501
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
USDA_API_KEY=your-usda-key
GEMINI_API_KEY=your-gemini-key
```

---

## 3. Database Setup (Supabase)
Run the complete SQL migration in your Supabase SQL Editor:
```bash
# Execute statements from:
db/schema.sql
```
This sets up tables (`logged_meals`, `meal_likes`, `shopping_list`, `chat_history`), indexes, Row Level Security (RLS) policies, and atomic RPC functions (`increment_meal_likes`, `get_top_loggers_last_7_days`).

---

## 4. Deployment Methods

### Option A: Docker Compose (Recommended for Multi-Service Orchestration)
Build and run both backend and frontend in isolated containers:

```bash
docker compose up -d --build
```

Inspect service health:
```bash
docker compose ps
docker compose logs -f
```

- Backend Healthcheck: `http://localhost:8000/health`
- Frontend UI: `http://localhost:8501`
- Interactive API Docs: `http://localhost:8000/docs`

### Option B: Bare-Metal / Virtual Environment

#### 1. Setup Environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Run Backend (FastAPI + Uvicorn)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 3. Run Frontend (Streamlit)
```bash
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 5. Production Health & Troubleshooting

| Check | Command | Expected Output |
|---|---|---|
| API Health | `curl -f http://localhost:8000/health` | `{"status":"healthy","model_loaded":true,...}` |
| Frontend Health | `curl -f http://localhost:8501/_stcore/health` | `ok` |
| Container Logs | `docker compose logs -f backend` | Structured JSON or formatted logs |
| Database Connectivity | Verified in `/health` output | `"supabase_configured":true` |

# 🥗 NutriLens - Production-Hardened Nutrition Tracking Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15+-orange.svg)
![Tests](https://img.shields.io/badge/Tests-23%20Passing-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An intelligent nutrition tracking platform powered by AI, computer vision, and machine learning**

[Architecture](ARCHITECTURE.md) • [Deployment](DEPLOYMENT.md) • [Testing](TESTING.md) • [Security](SECURITY.md) • [Remediation Report](ENGINEERING_REMEDIATION_REPORT.md)

</div>

---

## 🎯 Overview

NutriLens is a modern, production-grade nutrition intelligence application combining computer vision, machine learning, and asynchronous web services to help users analyze dietary intake, inspect barcode and ingredient labels, track macros, and collaborate in community feeds.

### Key Capabilities
- **🔍 AI Food Recognition**: Preprocessed image analysis with TensorFlow inference and USDA FoodData Central integration.
- **🛡️ Secure Nutrition Tracking**: Supabase JWT authentication, strict IDOR protection, and Row-Level Security.
- **🏪 Dual Scanner**: Dedicated barcode lookup (OpenFoodFacts) and nutrition label OCR analysis (Gemini Vision).
- **🤖 AI Chef Assistant**: Conversational recipe generator and smart grocery shopping list management.
- **👥 Atomic Community**: Public meal feed, atomic like counters with deduplication, and database-aggregated leaderboards.
- **📝 PDF Health Reports**: On-demand downloadable nutritional summaries.

---

## 🏗 Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full architectural documentation.

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                      │
│  (Tracker | Dashboard | AI Chef | Community | Scanner)       │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST API (Bearer <Supabase_JWT>)
┌───────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth & IDOR  │  │ ML Model     │  │ Async USDA   │      │
│  │ Enforcement  │  │ (TensorFlow) │  │ Client       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Barcode      │  │ Gemini Vision│  │ Async Open   │      │
│  │ pyzbar       │  │ Label OCR    │  │ FoodFacts    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Supabase Database                         │
│  • logged_meals   • meal_likes (deduplication)               │
│  • shopping_list  • chat_history   • Row-Level Security      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/yourusername/NutriLens.git
cd NutriLens
cp .env.example .env
```
Edit `.env` with your actual Supabase, USDA, and Gemini credentials.

### 2. Database Initialization
Run `db/schema.sql` in your Supabase SQL Editor.

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```
- Frontend: `http://localhost:8501`
- Backend API Docs: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

### 4. Running Tests
```bash
pytest -v
```

---

## 📡 API Reference

| Endpoint | Method | Auth Required | Description |
|---|---|---|---|
| `/health` | GET | No | Service status, model status, and config flags |
| `/api/v1/analyze` | POST | No | Classifies food photo and fetches USDA nutrients |
| `/api/v1/log_meal` | POST | **Yes** (Bearer JWT) | Logs a meal (user ID enforced from JWT) |
| `/api/v1/history/{user_id}` | GET | **Yes** (Bearer JWT) | Returns meal history (IDOR protected) |
| `/api/v1/community/feed` | GET | No | Fetches latest public meals |
| `/api/v1/community/like` | POST | **Yes** (Bearer JWT) | Atomic like increment with deduplication |
| `/api/v1/community/leaderboard` | GET | No | Top 3 loggers in last 7 days |
| `/api/v1/scan_barcode` | POST | No | Decodes barcode or queries barcode number |
| `/api/v1/scan_label` | POST | No | Analyzes ingredients label with Gemini Vision |

---

## 📄 Documentation Links
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [SECURITY.md](SECURITY.md)
- [TESTING.md](TESTING.md)
- [ENGINEERING_REMEDIATION_REPORT.md](ENGINEERING_REMEDIATION_REPORT.md)

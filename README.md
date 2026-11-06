# NutriLens V2 — Production AI Food Recognition & Nutrition Tracker

NutriLens V2 is a full-stack, mobile-responsive nutrition intelligence web platform featuring microsecond food classification, USDA nutritional analysis, barcode scanning, and community meal sharing.

---

## 🌟 Key Features

- **⚡ Fast Food Recognition**: MobileNetV2 Food-101 model running on ONNX Runtime (~1.6 ms latency, 14.5 MB binary).
- **📊 Nutritional Breakdown**: Calories, protein, carbohydrates, and fats verified via USDA FoodData Central.
- **📱 Modern Responsive Frontend**: React 19, TypeScript, and TailwindCSS single-page application with instant view switching.
- **🔒 Secure Authentication**: Supabase GoTrue Auth with cryptographically verified JWT tokens and PostgreSQL Row Level Security (RLS).
- **🛒 Smart Groceries**: Persistent shopping list syncable directly from AI Chef recipes.
- **👨‍🍳 AI Chef Assistant**: Generative healthy recipes tailored to recognized ingredients and dietary objectives.
- **🏷️ Product & Label Scanner**: Barcode lookup via OpenFoodFacts and ingredient analysis via Gemini 1.5 Flash Vision.
- **📄 Instant PDF Reports**: Client-side health summary generation with zero server overhead.

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Automated Testing
Run the comprehensive 35-test automated backend test suite:
```bash
pytest -v
```

---

## 📚 Technical Documentation
- [Architecture & Design](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Security Model](SECURITY.md)
- [Model Benchmark & Performance](MODEL_BENCHMARK.md)
- [Zero-Cost Cloud Analysis](COST_ANALYSIS.md)
- [Environment Template](.env.example)

---

## 📄 License
MIT License.

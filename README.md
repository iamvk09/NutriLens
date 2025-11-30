# 🥗 NutriLens - AI-Powered Nutrition Tracking Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An intelligent nutrition tracking platform powered by AI, computer vision, and machine learning**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [API Reference](#-api-reference) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Frontend Features](#-frontend-features)
- [Database Schema](#-database-schema)
- [Deployment](#-deployment)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## 🎯 Overview

NutriLens is a comprehensive, AI-driven nutrition tracking platform that combines computer vision, machine learning, and modern web technologies to help users monitor their dietary intake, analyze food products, and achieve their health goals.

### Key Capabilities

- **🔍 AI Food Recognition**: Upload food images and get instant nutrition analysis
- **📊 Comprehensive Dashboard**: Track calories, macros, and nutrition trends
- **🤖 AI Chef Assistant**: Get personalized recipe recommendations and meal planning
- **🏪 Barcode Scanner**: Scan product barcodes for instant nutrition information
- **👥 Social Community**: Share meals, like posts, and compete on leaderboards
- **📝 PDF Reports**: Generate detailed health reports
- **🛒 Smart Shopping Lists**: AI-powered ingredient extraction and list management

---

## ✨ Features

### Core Features

- **Food Image Analysis**
  - Deep learning-based food recognition using TensorFlow/Keras
  - Automatic nutrition data retrieval from USDA FoodData Central API
  - Support for 100+ food categories
  - Portion size estimation

- **Nutrition Tracking**
  - Real-time calorie and macro tracking
  - Historical meal logging
  - Daily/weekly nutrition summaries
  - Goal setting and progress monitoring

- **AI-Powered Features**
  - Gemini AI integration for recipe generation
  - Intelligent ingredient extraction
  - Personalized diet recommendations
  - Health analysis and safety checks

- **Barcode Scanning**
  - Product recognition via barcode scanning
  - OpenFoodFacts API integration
  - NutriScore and NOVA group analysis
  - AI-powered ingredient safety analysis

- **Social Features**
  - Public meal sharing
  - Community feed with likes
  - Weekly leaderboards
  - User engagement metrics

- **Reporting & Analytics**
  - Interactive charts and visualizations
  - PDF health report generation
  - Export capabilities
  - Trend analysis

### Frontend Features

- **Modern Dark Theme UI**
  - Glassmorphism design
  - Responsive layout
  - Smooth animations
  - Intuitive navigation

- **Multi-Tab Interface**
  - Tracker: Food image upload and analysis
  - Dashboard: Analytics and visualizations
  - AI Chef: Conversational recipe assistant
  - Diet Planner: Weekly meal planning
  - Community: Social feed and leaderboards
  - Groceries: Smart shopping list management
  - Barcode Scanner: Product analysis

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.8+
- **ML/AI**: 
  - TensorFlow 2.15
  - Keras 2.15
  - Google Gemini AI
- **Database**: Supabase (PostgreSQL)
- **APIs**: 
  - USDA FoodData Central API
  - OpenFoodFacts API

### Frontend
- **Framework**: Streamlit
- **Visualization**: Plotly Express
- **PDF Generation**: FPDF
- **Barcode**: pyzbar

### Infrastructure
- **Authentication**: Supabase Auth (OAuth + Email)
- **Deployment**: Docker-ready
- **Server**: Uvicorn/Gunicorn

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                      │
│  (Tracker | Dashboard | AI Chef | Community | Groceries)     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP/REST API
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Image        │  │ ML Model     │  │ USDA API     │      │
│  │ Processing   │  │ (TensorFlow)│  │ Integration  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Barcode      │  │ Gemini AI    │  │ OpenFood    │      │
│  │ Scanner      │  │ Integration  │  │ Facts API   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ PostgreSQL
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Supabase Database                         │
│  • logged_meals  • shopping_list  • chat_history            │
│  • User auth     • Community data                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Supabase account (free tier available)
- USDA API key ([Get it here](https://fdc.nal.usda.gov/api-guide.html))
- Google Gemini API key (optional, for AI features)
- Trained ML model (`food_model.h5`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/NutriLens.git
   cd NutriLens
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   
   # USDA API
   USDA_API_KEY=your_usda_api_key
   
   # Google Gemini (Optional)
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Set up database**
   
   Run the following SQL in your Supabase SQL Editor:
   ```sql
   -- Create logged_meals table
   CREATE TABLE logged_meals (
     id SERIAL PRIMARY KEY,
     user_id TEXT NOT NULL,
     food_name TEXT NOT NULL,
     calories FLOAT NOT NULL,
     protein_g FLOAT NOT NULL,
     fat_g FLOAT NOT NULL,
     carb_g FLOAT NOT NULL,
     is_public BOOLEAN DEFAULT FALSE,
     likes_count INTEGER DEFAULT 0,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Create shopping_list table
   CREATE TABLE shopping_list (
     id SERIAL PRIMARY KEY,
     user_id TEXT NOT NULL,
     item TEXT NOT NULL,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Create chat_history table
   CREATE TABLE chat_history (
     id SERIAL PRIMARY KEY,
     user_id TEXT NOT NULL,
     role TEXT NOT NULL,
     content TEXT NOT NULL,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

6. **Add ML model**
   
   Place your trained Keras model at `models/food_model.h5`
   
   Optionally, create `models/class_names.json`:
   ```json
   {
     "0": "apple",
     "1": "banana",
     "2": "orange"
   }
   ```

7. **Run the application**
   
   **Backend (Terminal 1):**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   **Frontend (Terminal 2):**
   ```bash
   streamlit run streamlit_app.py
   ```

8. **Access the application**
   - Frontend: http://localhost:8501
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Your Supabase anon/service key | Yes |
| `USDA_API_KEY` | USDA FoodData Central API key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | No (for AI features) |

### ML Model Configuration

- **Model Format**: Keras H5 format
- **Input Size**: 224x224 RGB images
- **Preprocessing**: Normalized to [0, 1]
- **Class Names**: Optional JSON mapping file

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. Analyze Food Image
```http
POST /api/v1/analyze
Content-Type: multipart/form-data
```

**Request**: Image file (JPEG, PNG, etc.)

**Response**:
```json
{
  "food_name": "apple",
  "calories": 52.0,
  "protein_g": 0.3,
  "fat_g": 0.2,
  "carb_g": 14.0
}
```

#### 2. Log Meal
```http
POST /api/v1/log_meal
Content-Type: application/json
```

**Request**:
```json
{
  "user_id": "user123",
  "food_name": "apple",
  "calories": 52.0,
  "protein_g": 0.3,
  "fat_g": 0.2,
  "carb_g": 14.0,
  "is_public": false
}
```

**Response**:
```json
{
  "message": "Meal logged successfully"
}
```

#### 3. Get User History
```http
GET /api/v1/history/{user_id}
```

**Response**: Array of meal objects

#### 4. Community Feed
```http
GET /api/v1/community/feed
```

**Response**: Array of public meals (last 20)

#### 5. Like Meal
```http
POST /api/v1/community/like
Content-Type: application/json
```

**Request**:
```json
{
  "meal_id": 123
}
```

#### 6. Leaderboard
```http
GET /api/v1/community/leaderboard
```

**Response**: Top 3 users with most meals in last 7 days

#### 7. Scan Barcode
```http
POST /api/v1/scan_barcode
Content-Type: multipart/form-data
```

**Request**: Barcode image OR barcode number

**Response**:
```json
{
  "barcode": "3017620422003",
  "product_name": "Product Name",
  "brand": "Brand Name",
  "nutriscore_grade": "A",
  "nova_group": 1,
  "ingredients_text": "...",
  "allergens": "...",
  "image_url": "..."
}
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🎨 Frontend Features

### Tracker Tab
- Upload food images
- Portion size adjustment
- Instant nutrition analysis
- Share to community option

### Dashboard Tab
- Nutrition metrics and trends
- Interactive charts (Plotly)
- Meal history table
- PDF report generation

### AI Chef Tab
- Conversational recipe assistant
- Context-aware responses
- Ingredient extraction
- Recipe-to-shopping-list conversion

### Diet Planner Tab
- Goal-based meal planning
- 7-day diet plans
- Customizable targets

### Community Tab
- Public meal feed
- Like functionality
- Weekly leaderboards
- User engagement

### Groceries Tab
- Manual item addition
- AI-powered ingredient import
- List management
- Bulk operations

### Barcode Scanner Tab
- Image or manual barcode input
- Product information display
- Health indicators (NutriScore, NOVA)
- AI safety analysis

---

## 🗄 Database Schema

### `logged_meals`
```sql
CREATE TABLE logged_meals (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  food_name TEXT NOT NULL,
  calories FLOAT NOT NULL,
  protein_g FLOAT NOT NULL,
  fat_g FLOAT NOT NULL,
  carb_g FLOAT NOT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  likes_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### `shopping_list`
```sql
CREATE TABLE shopping_list (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  item TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### `chat_history`
```sql
CREATE TABLE chat_history (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚢 Deployment

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t nutrilens .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 -p 8501:8501 --env-file .env nutrilens
   ```

### Production Deployment

**Backend (FastAPI)**
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend (Streamlit)**
```bash
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### Environment Variables for Production

Ensure all environment variables are set in your production environment. Consider using:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Environment variables in your hosting platform

---

## 💻 Development

### Project Structure

```
NutriLens/
├── main.py                 # FastAPI backend application
├── streamlit_app.py        # Streamlit frontend application
├── schemas.py              # Pydantic models for validation
├── model_utils.py          # ML model utilities
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── models/                # ML model directory
    ├── food_model.h5      # Trained Keras model
    └── class_names.json   # Class name mappings
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

This project follows PEP 8 style guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guide
- Write clear commit messages
- Add tests for new features
- Update documentation
- Ensure all tests pass

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Supabase Documentation](https://supabase.com/docs)

### Issues
If you encounter any issues, please [open an issue](https://github.com/yourusername/NutriLens/issues) on GitHub.

### Contact
- **Email**: support@nutrilens.com
- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Discord**: [Join our community](https://discord.gg/nutrilens)

---

## 🙏 Acknowledgments

- [USDA FoodData Central](https://fdc.nal.usda.gov/) for nutrition data
- [OpenFoodFacts](https://world.openfoodfacts.org/) for product information
- [Supabase](https://supabase.com/) for backend infrastructure
- [TensorFlow](https://www.tensorflow.org/) for ML capabilities
- [Google Gemini](https://ai.google.dev/) for AI features

---

<div align="center">

**Made with ❤️ by the NutriLens Team**

⭐ Star this repo if you find it helpful!

</div>

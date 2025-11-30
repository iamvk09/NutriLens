"""
NutriLens FastAPI Backend
Main application file with ML model integration and API endpoints
"""

import os
import io
from pathlib import Path
from typing import Optional

import numpy as np
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from supabase import create_client, Client
import tensorflow as tf
from tensorflow import keras
from pyzbar.pyzbar import decode as pyzbar_decode

from schemas import AnalyzeResponse, LogMealRequest, LogMealResponse, LikeRequest
from model_utils import predict_food_name as predict_food_name_util, get_class_names

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="NutriLens API",
    description="Food image analysis and nutrition tracking API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for ML model and Supabase client
ML_MODEL: Optional[keras.Model] = None
SUPABASE_CLIENT: Optional[Client] = None

# Environment variables
USDA_API_KEY = os.getenv("USDA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client() -> Client:
    """Dependency to get Supabase client"""
    global SUPABASE_CLIENT
    if SUPABASE_CLIENT is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise HTTPException(
                status_code=500,
                detail="Supabase configuration not found in environment variables"
            )
        SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)
    return SUPABASE_CLIENT


def load_ml_model():
    """Load the Keras model on application startup"""
    global ML_MODEL
    model_path = Path("./models/food_model.h5")
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found at {model_path}. "
            "Please ensure the model is saved at './models/food_model.h5'"
        )
    
    try:
        ML_MODEL = keras.models.load_model(str(model_path))
        print(f"✓ ML model loaded successfully from {model_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load ML model: {str(e)}")


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess image for ML model input.
    Resizes to 224x224 and normalizes pixel values.
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize to 224x224
        image = image.resize((224, 224))
        
        # Convert to numpy array and normalize
        img_array = np.array(image, dtype=np.float32)
        img_array = img_array / 255.0  # Normalize to [0, 1]
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to preprocess image: {str(e)}"
        )


def predict_food_name(image_array: np.ndarray) -> str:
    """
    Use ML model to predict food name from preprocessed image.
    Returns the predicted food name as a string.
    """
    global ML_MODEL
    
    if ML_MODEL is None:
        raise HTTPException(
            status_code=500,
            detail="ML model not loaded"
        )
    
    try:
        # Get class names mapping if available
        class_names = get_class_names()
        
        # Use utility function for prediction
        predicted_food_name = predict_food_name_util(ML_MODEL, image_array, class_names)
        
        return predicted_food_name
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


def fetch_usda_nutrition(food_name: str) -> dict:
    """
    Fetch nutrition data from USDA FoodData Central API.
    Returns dictionary with calories, protein_g, fat_g, carb_g.
    """
    if not USDA_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="USDA API key not configured"
        )
    
    usda_api_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    
    params = {
        "query": food_name,
        "api_key": USDA_API_KEY,
        "pageSize": 1
    }
    
    try:
        response = requests.get(usda_api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse USDA response
        if not data.get("foods") or len(data["foods"]) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No nutrition data found for '{food_name}'"
            )
        
        food_item = data["foods"][0]
        nutrients = food_item.get("foodNutrients", [])
        
        # Extract nutrition values
        nutrition_data = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carb_g": 0.0
        }
        
        # USDA API nutrient IDs (more reliable than names)
        # Reference: https://fdc.nal.usda.gov/api-guide.html
        nutrient_id_map = {
            "calories": [1008, 1062],  # Energy (kcal), Energy (Atwater General Factors)
            "protein_g": [1003],       # Protein
            "fat_g": [1004],           # Total lipid (fat)
            "carb_g": [1005]           # Carbohydrate, by difference
        }
        
        # Also match by name as fallback
        nutrient_name_map = {
            "calories": ["Energy", "Energy (Atwater General Factors)", "Energy (kcal)"],
            "protein_g": ["Protein"],
            "fat_g": ["Total lipid (fat)", "Fat, total"],
            "carb_g": ["Carbohydrate, by difference", "Carbohydrates", "Carbohydrate"]
        }
        
        for nutrient in nutrients:
            nutrient_id = nutrient.get("nutrientId")
            nutrient_name = nutrient.get("nutrientName", "").strip()
            value = nutrient.get("value", 0.0)
            unit = nutrient.get("unitName", "").strip()
            
            # Skip if no valid value
            if value is None or (isinstance(value, (int, float)) and value == 0):
                continue
            
            value = float(value)
            
            # Match by nutrient ID first (more reliable)
            if nutrient_id in nutrient_id_map.get("calories", []):
                # Ensure calories are in kcal
                if unit.lower() in ["kcal", "kilocalories"] or nutrient_id == 1008:
                    nutrition_data["calories"] = value
            elif nutrient_id in nutrient_id_map.get("protein_g", []):
                nutrition_data["protein_g"] = value
            elif nutrient_id in nutrient_id_map.get("fat_g", []):
                nutrition_data["fat_g"] = value
            elif nutrient_id in nutrient_id_map.get("carb_g", []):
                nutrition_data["carb_g"] = value
            # Fallback: match by name (for cases where ID might not match)
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map.get("calories", [])):
                if not nutrition_data["calories"] or nutrition_data["calories"] == 0:
                    nutrition_data["calories"] = value
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map.get("protein_g", [])):
                if not nutrition_data["protein_g"] or nutrition_data["protein_g"] == 0:
                    nutrition_data["protein_g"] = value
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map.get("fat_g", [])):
                if not nutrition_data["fat_g"] or nutrition_data["fat_g"] == 0:
                    nutrition_data["fat_g"] = value
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map.get("carb_g", [])):
                if not nutrition_data["carb_g"] or nutrition_data["carb_g"] == 0:
                    nutrition_data["carb_g"] = value
        
        return nutrition_data
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"USDA API request failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse USDA response: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Load ML model on application startup"""
    try:
        load_ml_model()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Application will start but /analyze endpoint will not work until model is available.")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NutriLens API is running",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "log_meal": "/api/v1/log_meal",
            "history": "/api/v1/history/{user_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": ML_MODEL is not None,
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY),
        "usda_configured": bool(USDA_API_KEY)
    }


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_food_image(
    file: UploadFile = File(...)
):
    """
    Analyze food image and return nutrition information.
    
    - **file**: Image file (JPEG, PNG, etc.) to analyze
    - Returns: Food name and nutrition data (calories, protein, fat, carbs)
    """
    if ML_MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="ML model is not loaded. Please check server logs."
        )
    
    # Read image file
    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read image file: {str(e)}"
        )
    
    # Preprocess image
    image_array = preprocess_image(image_bytes)
    
    # Predict food name
    predicted_food_name = predict_food_name(image_array)
    
    # Fetch nutrition data from USDA API
    nutrition_data = fetch_usda_nutrition(predicted_food_name)
    
    # Return response
    return AnalyzeResponse(
        food_name=predicted_food_name,
        calories=nutrition_data["calories"],
        protein_g=nutrition_data["protein_g"],
        fat_g=nutrition_data["fat_g"],
        carb_g=nutrition_data["carb_g"]
    )


@app.post("/api/v1/log_meal", response_model=LogMealResponse)
async def log_meal(
    meal_data: LogMealRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Log analyzed meal data to Supabase database.
    
    - **meal_data**: JSON body with meal information
    - Returns: Success message
    """
    try:
        # Insert meal data into Supabase
        result = supabase.table("logged_meals").insert({
            "user_id": meal_data.user_id,
            "food_name": meal_data.food_name,
            "calories": meal_data.calories,
            "protein_g": meal_data.protein_g,
            "fat_g": meal_data.fat_g,
            "carb_g": meal_data.carb_g,
            "is_public": meal_data.is_public
        }).execute()
        
        return LogMealResponse(
            message="Meal logged successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log meal: {str(e)}"
        )

# --- NEW ENDPOINT: Get User History ---
@app.get("/api/v1/history/{user_id}")
async def get_history(
    user_id: str,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Fetch the last 50 meals for this user, newest first.
    """
    try:
        # Fetch data from Supabase 'logged_meals' table
        response = supabase.table("logged_meals")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- COMMUNITY ENDPOINTS ---

@app.get("/api/v1/community/feed")
async def get_community_feed(
    supabase: Client = Depends(get_supabase_client)
):
    """
    Fetch the last 20 public meals from the community, ordered by created_at desc.
    """
    try:
        response = supabase.table("logged_meals")\
            .select("*")\
            .eq("is_public", True)\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch community feed: {str(e)}"
        )


@app.post("/api/v1/community/like")
async def like_meal(
    like_data: LikeRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Increment likes_count for a meal by 1.
    """
    try:
        # First, get the current likes_count
        meal_response = supabase.table("logged_meals")\
            .select("likes_count")\
            .eq("id", like_data.meal_id)\
            .execute()
        
        if not meal_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Meal with id {like_data.meal_id} not found"
            )
        
        current_likes = meal_response.data[0].get("likes_count", 0) or 0
        
        # Increment likes_count by 1
        update_response = supabase.table("logged_meals")\
            .update({"likes_count": current_likes + 1})\
            .eq("id", like_data.meal_id)\
            .execute()
        
        return {
            "message": "Meal liked successfully",
            "meal_id": like_data.meal_id,
            "new_likes_count": current_likes + 1
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to like meal: {str(e)}"
        )


@app.get("/api/v1/community/leaderboard")
async def get_leaderboard(
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get top 3 users with the most logged meals in the last 7 days.
    """
    try:
        from datetime import datetime, timedelta
        
        # Calculate date 7 days ago
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Fetch meals from the last 7 days
        response = supabase.table("logged_meals")\
            .select("user_id")\
            .gte("created_at", seven_days_ago.isoformat())\
            .execute()
        
        # Count meals per user
        from collections import Counter
        user_counts = Counter(meal["user_id"] for meal in response.data)
        
        # Get top 3 users
        top_users = user_counts.most_common(3)
        
        # Format response
        leaderboard = [
            {
                "rank": idx + 1,
                "user_id": user_id,
                "score": count
            }
            for idx, (user_id, count) in enumerate(top_users)
        ]
        
        # Pad to 3 entries if less than 3 users
        while len(leaderboard) < 3:
            leaderboard.append({
                "rank": len(leaderboard) + 1,
                "user_id": None,
                "score": 0
            })
        
        return leaderboard
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch leaderboard: {str(e)}"
        )


@app.post("/api/v1/scan_barcode")
async def scan_barcode(
    file: Optional[UploadFile] = File(None),
    barcode_number: Optional[str] = Form(None)
):
    """
    Scan barcode from image or use provided barcode number to fetch product data.
    
    - **file**: Image file containing barcode (optional if barcode_number provided as query param)
    - **barcode_number**: Direct barcode number (optional query param if file provided)
    - Returns: Product information from OpenFoodFacts API
    """
    barcode = None
    
    # If file is provided, decode barcode from image
    if file and file.filename:
        try:
            image_bytes = await file.read()
            if len(image_bytes) == 0:
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary (pyzbar requires RGB)
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Decode barcode
            decoded_objects = pyzbar_decode(image)
            
            if not decoded_objects:
                raise HTTPException(
                    status_code=400,
                    detail="No barcode found in image. Please ensure the barcode is clear and visible."
                )
            
            # Get the first barcode data
            barcode = decoded_objects[0].data.decode("utf-8")
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to decode barcode from image: {str(e)}"
            )
    
    # Use provided barcode number if no file or if file decoding failed
    if not barcode and barcode_number:
        barcode = barcode_number.strip()
    
    if not barcode:
        raise HTTPException(
            status_code=400,
            detail="No barcode provided. Please upload an image or enter a barcode number."
        )
    
    # Fetch product data from OpenFoodFacts API
    try:
        api_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found for barcode: {barcode}"
            )
        
        product = data.get("product", {})
        
        # Extract product information
        result = {
            "barcode": barcode,
            "product_name": product.get("product_name", product.get("product_name_en", "Unknown Product")),
            "brand": product.get("brands", "").split(",")[0].strip() if product.get("brands") else "Unknown Brand",
            "nutriscore_grade": product.get("nutriscore_grade", "").upper() if product.get("nutriscore_grade") else None,
            "nova_group": product.get("nova_group", None),
            "ingredients_text": product.get("ingredients_text", ""),
            "allergens": product.get("allergens", ""),
            "image_url": product.get("image_url", product.get("image_front_url", ""))
        }
        
        return result
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"OpenFoodFacts API request failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process barcode: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

    # --- ADD THIS TO main.py ---

@app.post("/api/v1/scan_label")
async def scan_label(file: UploadFile = File(...)):
    """
    Fallback: Uses Gemini Vision to read the ingredients label directly.
    """
    try:
        # Read image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Prompt for Gemini
        prompt = """
        Read the text in this image. It is a food product label.
        1. Extract the 'Ingredients List' exactly as written.
        2. Extract the 'Nutritional Information' (Calories, Protein, etc) if visible.
        3. Analyze the ingredients: Are there harmful additives? High sugar?
        4. Return STRICT JSON:
        {
            "product_name": "Unknown (Detected from label)",
            "ingredients_text": "...",
            "is_healthy": true/false,
            "health_rating": "A/B/C/D/E (Estimate)",
            "warnings": ["List of bad ingredients"],
            "positive_points": ["List of good points"]
        }
        """
        
        
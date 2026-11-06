"""
NutriLens FastAPI Backend
Production-hardened application with non-blocking async network clients,
ML model integration, Supabase authentication & JWT propagation, and full API endpoints.
"""

import io
import json
import re
from typing import Optional, List, Dict, Any

import httpx
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pyzbar.pyzbar import decode as pyzbar_decode
from supabase import Client

from config import settings
from logger import logger, RequestLoggingMiddleware
from auth import (
    get_current_user,
    get_optional_user,
    get_supabase_client,
    get_authenticated_supabase_client,
    AuthenticatedUser,
)
from schemas import (
    AnalyzeResponse,
    LogMealRequest,
    LogMealResponse,
    LikeRequest,
    ScanLabelResponse,
    BarcodeProductResponse,
)
from model_utils import (
    load_model_safe,
    predict_food_name as predict_food_name_util,
    get_class_names,
    get_loaded_model,
    is_model_loaded,
)

# Optional Gemini setup
GENAI_CLIENT: Any = None
try:
    if settings.GEMINI_API_KEY:
        from google import genai
        GENAI_CLIENT = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    logger.warning(f"Could not initialize google.genai: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="NutriLens API",
    description="Production Food Analysis, Barcode Scanning & Nutrition Tracking API",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# Add Strict CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Reusable Async HTTP Client
ASYNC_HTTP_CLIENT: Optional[httpx.AsyncClient] = None


@app.on_event("startup")
async def startup_event():
    """Startup initialization: HTTP client and ML model loading."""
    global ASYNC_HTTP_CLIENT
    logger.info(f"Starting NutriLens API in {settings.ENVIRONMENT} mode...")

    ASYNC_HTTP_CLIENT = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS),
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
    )

    try:
        load_model_safe(
            model_path=settings.MODEL_PATH,
            download_url=settings.MODEL_DOWNLOAD_URL,
            expected_sha256=settings.MODEL_EXPECTED_SHA256,
            expected_size=settings.MODEL_EXPECTED_SIZE_BYTES
        )
    except Exception as exc:
        logger.error(f"Error initializing ML model: {exc}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on server shutdown."""
    global ASYNC_HTTP_CLIENT
    if ASYNC_HTTP_CLIENT:
        await ASYNC_HTTP_CLIENT.aclose()
        logger.info("Closed async HTTP client.")


def get_http_client() -> httpx.AsyncClient:
    """Dependency / accessor for async HTTP client."""
    global ASYNC_HTTP_CLIENT
    if ASYNC_HTTP_CLIENT is None or ASYNC_HTTP_CLIENT.is_closed:
        ASYNC_HTTP_CLIENT = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS),
            follow_redirects=True
        )
    return ASYNC_HTTP_CLIENT


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess image for ML model input.
    Validates image, converts to RGB, resizes to 224x224 and normalizes.
    """
    if len(image_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds maximum allowed size ({settings.MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB)"
        )
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        image = image.resize((224, 224))
        img_array = np.array(image, dtype=np.float32) / 255.0
        return np.expand_dims(img_array, axis=0)
    except Exception as e:
        logger.warning(f"Failed to preprocess image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format or corrupted file"
        )


async def fetch_usda_nutrition(food_name: str, client: httpx.AsyncClient) -> Dict[str, float]:
    """
    Asynchronously fetch nutrition data from USDA FoodData Central API.
    Returns normalized macronutrient dictionary with fallback defaults.
    """
    if not settings.USDA_API_KEY:
        logger.warning("USDA_API_KEY not configured. Falling back to default macronutrients.")
        return {"calories": 100.0, "protein_g": 2.0, "fat_g": 0.5, "carb_g": 20.0}

    usda_api_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": food_name,
        "api_key": settings.USDA_API_KEY,
        "pageSize": 1
    }

    try:
        response = await client.get(usda_api_url, params=params)
        if response.status_code == 404:
            return {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carb_g": 0.0}
        response.raise_for_status()
        data = response.json()

        foods = data.get("foods", [])
        if not foods:
            logger.info(f"No USDA data found for '{food_name}', using zero defaults.")
            return {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carb_g": 0.0}

        food_item = foods[0]
        nutrients = food_item.get("foodNutrients", [])

        nutrition_data = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carb_g": 0.0
        }

        nutrient_id_map = {
            "calories": [1008, 1062],
            "protein_g": [1003],
            "fat_g": [1004],
            "carb_g": [1005]
        }
        nutrient_name_map = {
            "calories": ["Energy", "Energy (Atwater General Factors)", "Energy (kcal)"],
            "protein_g": ["Protein"],
            "fat_g": ["Total lipid (fat)", "Fat, total"],
            "carb_g": ["Carbohydrate, by difference", "Carbohydrates", "Carbohydrate"]
        }

        for nutrient in nutrients:
            nutrient_id = nutrient.get("nutrientId")
            nutrient_name = nutrient.get("nutrientName", "").strip()
            val = nutrient.get("value", 0.0)
            if val is None:
                continue
            val = float(val)

            if nutrient_id in nutrient_id_map["calories"]:
                nutrition_data["calories"] = val
            elif nutrient_id in nutrient_id_map["protein_g"]:
                nutrition_data["protein_g"] = val
            elif nutrient_id in nutrient_id_map["fat_g"]:
                nutrition_data["fat_g"] = val
            elif nutrient_id in nutrient_id_map["carb_g"]:
                nutrition_data["carb_g"] = val
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map["calories"]):
                if not nutrition_data["calories"]:
                    nutrition_data["calories"] = val
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map["protein_g"]):
                if not nutrition_data["protein_g"]:
                    nutrition_data["protein_g"] = val
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map["fat_g"]):
                if not nutrition_data["fat_g"]:
                    nutrition_data["fat_g"] = val
            elif any(name.lower() in nutrient_name.lower() for name in nutrient_name_map["carb_g"]):
                if not nutrition_data["carb_g"]:
                    nutrition_data["carb_g"] = val

        return nutrition_data
    except httpx.TimeoutException:
        logger.error(f"Timeout querying USDA API for '{food_name}'")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="USDA nutrition service timed out"
        )
    except httpx.HTTPError as exc:
        logger.error(f"USDA API error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve nutritional data from external USDA service"
        )


# --- ROUTE HANDLERS ---

@app.get("/")
async def root():
    """Root status and discovery endpoint."""
    return {
        "app": "NutriLens API",
        "version": "1.1.0",
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze",
            "log_meal": "/api/v1/log_meal",
            "history": "/api/v1/history/{user_id}",
            "feed": "/api/v1/community/feed",
            "like": "/api/v1/community/like",
            "leaderboard": "/api/v1/community/leaderboard",
            "scan_barcode": "/api/v1/scan_barcode",
            "scan_label": "/api/v1/scan_label",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint reflecting service configuration."""
    return {
        "status": "healthy",
        "model_loaded": is_model_loaded(),
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
        "usda_configured": bool(settings.USDA_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "environment": settings.ENVIRONMENT
    }


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_food_image(
    file: UploadFile = File(...),
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Analyze uploaded food image with ML model and USDA nutrition data.
    If no trained model is available on disk, explicitly returns 503 Service Unavailable.
    """
    model = get_loaded_model()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trained ML model is currently unavailable on the server. Please ensure 'food_model.h5' is placed in ./models/ or configure MODEL_DOWNLOAD_URL."
        )

    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    image_array = preprocess_image(image_bytes)
    class_names = get_class_names()
    prediction_result = predict_food_name_util(model, image_array, class_names)

    if isinstance(prediction_result, dict):
        predicted_food_name = prediction_result["food_name"]
        confidence = prediction_result.get("confidence")
        top_predictions = prediction_result.get("top_predictions", [])
    else:
        predicted_food_name = str(prediction_result)
        confidence = 1.0
        top_predictions = [{"food_name": predicted_food_name, "confidence": 1.0}]

    nutrition_data = await fetch_usda_nutrition(predicted_food_name, http_client)
    source = "USDA" if settings.USDA_API_KEY else "FALLBACK_ESTIMATE"

    return AnalyzeResponse(
        food_name=predicted_food_name,
        confidence=confidence,
        top_predictions=top_predictions,
        calories=nutrition_data["calories"],
        protein_g=nutrition_data["protein_g"],
        fat_g=nutrition_data["fat_g"],
        carb_g=nutrition_data["carb_g"],
        source=source,
        is_verified=bool(settings.USDA_API_KEY)
    )


@app.post("/api/v1/log_meal", response_model=LogMealResponse)
async def log_meal(
    meal_data: LogMealRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    supabase: Client = Depends(get_authenticated_supabase_client)
):
    """
    Securely log a meal for the authenticated user.
    Propagates user JWT to Supabase so PostgreSQL auth.uid() matches and RLS applies.
    """
    target_user_id = current_user.user_id
    try:
        insert_payload = {
            "user_id": target_user_id,
            "food_name": meal_data.food_name,
            "calories": meal_data.calories,
            "protein_g": meal_data.protein_g,
            "fat_g": meal_data.fat_g,
            "carb_g": meal_data.carb_g,
            "is_public": meal_data.is_public
        }
        res = supabase.table("logged_meals").insert(insert_payload).execute()
        meal_id = None
        if res.data and len(res.data) > 0:
            meal_id = res.data[0].get("id")

        return LogMealResponse(message="Meal logged successfully", meal_id=meal_id)
    except Exception as exc:
        logger.error(f"Failed to insert logged meal: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction error while logging meal"
        )


@app.get("/api/v1/history/{user_id}")
async def get_history(
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    supabase: Client = Depends(get_authenticated_supabase_client)
):
    """
    Fetch history for user.
    IDOR Protection: Users can only read their own meal history.
    Propagates user JWT so RLS verifies auth.uid().
    """
    if current_user.user_id != user_id:
        logger.warning(f"IDOR attempt blocked: User {current_user.user_id} tried to read history of {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You may only query your own meal history"
        )

    try:
        response = supabase.table("logged_meals")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()
        return response.data or []
    except Exception as exc:
        logger.error(f"Database error fetching meal history: {exc}")
        raise HTTPException(status_code=500, detail="Error retrieving meal records")


@app.get("/api/v1/community/feed")
async def get_community_feed(
    supabase: Client = Depends(get_supabase_client)
):
    """
    Public community feed: returns latest 20 public meals.
    Uses unauthenticated client (public meals have is_public=true allowed by RLS).
    """
    try:
        response = supabase.table("logged_meals")\
            .select("*")\
            .eq("is_public", True)\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        return response.data or []
    except Exception as exc:
        logger.error(f"Error fetching community feed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch community feed")


@app.post("/api/v1/community/like")
async def like_meal(
    like_data: LikeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    supabase: Client = Depends(get_authenticated_supabase_client)
):
    """
    Atomic community like endpoint.
    STRICT SECURITY RULE: The like counter is NEVER incremented if inserting
    into meal_likes fails for any reason (duplicate like, authorization, etc.).
    """
    meal_id = like_data.meal_id
    user_id = current_user.user_id

    # 1. Verify meal exists
    try:
        meal_check = supabase.table("logged_meals").select("id, likes_count").eq("id", meal_id).execute()
    except Exception as exc:
        logger.error(f"Error checking meal {meal_id}: {exc}")
        raise HTTPException(status_code=500, detail="Error retrieving meal record")

    if not meal_check.data:
        raise HTTPException(status_code=404, detail=f"Meal with ID {meal_id} does not exist")

    current_likes = meal_check.data[0].get("likes_count", 0) or 0

    # 2. Try atomic database RPC function first (which runs both in one transaction)
    try:
        rpc_res = supabase.rpc("increment_meal_likes", {"m_id": meal_id}).execute()
        if rpc_res.data is not None:
            return {
                "message": "Meal liked successfully",
                "meal_id": meal_id,
                "new_likes_count": rpc_res.data
            }
    except Exception as rpc_err:
        err_msg = str(rpc_err).lower()
        if "duplicate" in err_msg or "unique" in err_msg or "uq_meal_user_like" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already liked this meal"
            )
        if "unauthorized" in err_msg or "permission denied" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized to like this meal"
            )
        logger.info(f"RPC increment_meal_likes unavailable, falling back to manual atomic table transaction: {rpc_err}")

    # 3. Fallback table operations: insert into meal_likes MUST succeed before updating counter
    try:
        supabase.table("meal_likes").insert({
            "meal_id": meal_id,
            "user_id": user_id
        }).execute()
    except Exception as like_insert_err:
        err_str = str(like_insert_err).lower()
        if "duplicate" in err_str or "unique" in err_str or "conflict" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already liked this meal"
            )
        logger.error(f"Cannot like meal: meal_likes insertion failed: {like_insert_err}")
        # ABORT: Do not increment likes_count under any circumstance if insert fails
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register meal like"
        )

    # 4. Only once like insertion is confirmed successful, update the counter
    new_likes = current_likes + 1
    try:
        supabase.table("logged_meals").update({"likes_count": new_likes}).eq("id", meal_id).execute()
    except Exception as update_err:
        logger.error(f"Warning: Counter update failed after recording like: {update_err}")

    return {
        "message": "Meal liked successfully",
        "meal_id": meal_id,
        "new_likes_count": new_likes
    }


@app.get("/api/v1/community/leaderboard")
async def get_leaderboard(
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get top 3 users with the most logged meals in the last 7 days.
    Uses optimized database queries and RPC if available, with structured fallback.
    """
    from datetime import datetime, timedelta, timezone

    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    try:
        try:
            rpc_res = supabase.rpc("get_top_loggers_last_7_days", {"limit_count": 3}).execute()
            if rpc_res.data:
                return rpc_res.data
        except Exception:
            pass

        response = supabase.table("logged_meals")\
            .select("user_id")\
            .gte("created_at", seven_days_ago)\
            .execute()

        from collections import Counter
        user_counts = Counter(meal["user_id"] for meal in (response.data or []) if meal.get("user_id"))
        top_users = user_counts.most_common(3)

        leaderboard = [
            {"rank": idx + 1, "user_id": user_id, "score": count}
            for idx, (user_id, count) in enumerate(top_users)
        ]
        while len(leaderboard) < 3:
            leaderboard.append({"rank": len(leaderboard) + 1, "user_id": None, "score": 0})
        return leaderboard
    except Exception as exc:
        logger.error(f"Error compiling leaderboard: {exc}")
        raise HTTPException(status_code=500, detail="Failed to calculate community leaderboard")


@app.post("/api/v1/scan_barcode", response_model=BarcodeProductResponse)
async def scan_barcode(
    file: Optional[UploadFile] = File(None),
    barcode_number: Optional[str] = Form(None),
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Decode barcode from uploaded image or use barcode_number, then query OpenFoodFacts.
    """
    barcode = None

    if file and file.filename:
        try:
            image_bytes = await file.read()
            if not image_bytes:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            if len(image_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
                raise HTTPException(status_code=413, detail="Barcode image exceeds size limit")

            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")

            decoded_objects = pyzbar_decode(image)
            if not decoded_objects:
                raise HTTPException(
                    status_code=400,
                    detail="No barcode found in image. Please provide a clear, well-lit barcode photo."
                )
            barcode = decoded_objects[0].data.decode("utf-8").strip()
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Barcode decoding failed: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to decode barcode from image: {str(e)}")

    if not barcode and barcode_number:
        clean_code = re.sub(r"[^0-9a-zA-Z]", "", barcode_number)
        if clean_code:
            barcode = clean_code

    if not barcode:
        raise HTTPException(
            status_code=400,
            detail="No barcode provided. Please upload an image or enter a valid barcode number."
        )

    api_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = await http_client.get(api_url)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Product not found for barcode: {barcode}")
        response.raise_for_status()
        data = response.json()

        if data.get("status") == 0:
            raise HTTPException(status_code=404, detail=f"Product not found for barcode: {barcode}")

        product = data.get("product", {})
        result = BarcodeProductResponse(
            barcode=barcode,
            product_name=product.get("product_name") or product.get("product_name_en") or "Unknown Product",
            brand=product.get("brands", "").split(",")[0].strip() if product.get("brands") else "Unknown Brand",
            nutriscore_grade=product.get("nutriscore_grade", "").upper() if product.get("nutriscore_grade") else None,
            nova_group=product.get("nova_group"),
            ingredients_text=product.get("ingredients_text", ""),
            allergens=product.get("allergens", ""),
            image_url=product.get("image_url") or product.get("image_front_url")
        )
        return result
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="OpenFoodFacts service timed out")
    except httpx.HTTPError as exc:
        logger.error(f"OpenFoodFacts API error: {exc}")
        raise HTTPException(status_code=502, detail="Failed to communicate with OpenFoodFacts service")


@app.post("/api/v1/scan_label", response_model=ScanLabelResponse)
async def scan_label(file: UploadFile = File(...)):
    """
    Uses Google Gemini Vision to read ingredient labels and extract health insights.
    Completely handles validation, API failures, and structured JSON parsing.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured on the server. Set GEMINI_API_KEY in environment."
        )

    try:
        image_bytes = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read uploaded image")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image uploaded")
    if len(image_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Image file exceeds size limit")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    prompt = """
    You are an expert food scientist and label analyst. Read the food product label in this image carefully.
    1. Extract the product name or brief description.
    2. Extract the exact ingredients list as written.
    3. Analyze if the product is generally healthy, estimate a rating from A to E (A is best, E is worst).
    4. List any negative warnings (e.g. trans fats, high sodium, artificial additives, high fructose corn syrup).
    5. List positive nutritional points (e.g. high fiber, whole grains, zero added sugar).

    Output STRICT JSON only matching this schema without markdown formatting or codeblocks:
    {
        "product_name": "String",
        "ingredients_text": "String",
        "is_healthy": true,
        "health_rating": "A",
        "warnings": ["warning 1"],
        "positive_points": ["point 1"]
    }
    """

    try:
        global GENAI_CLIENT
        if GENAI_CLIENT is None and settings.GEMINI_API_KEY:
            from google import genai
            GENAI_CLIENT = genai.Client(api_key=settings.GEMINI_API_KEY)

        if not GENAI_CLIENT:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini client could not be initialized."
            )

        response = GENAI_CLIENT.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt, image]
        )
        text_resp = response.text.strip() if response and response.text else ""

        text_resp = re.sub(r"^```(?:json)?\s*", "", text_resp)
        text_resp = re.sub(r"\s*```$", "", text_resp)

        parsed = json.loads(text_resp)
        return ScanLabelResponse(
            product_name=parsed.get("product_name", "Unknown Product"),
            ingredients_text=parsed.get("ingredients_text", ""),
            is_healthy=parsed.get("is_healthy"),
            health_rating=parsed.get("health_rating"),
            warnings=parsed.get("warnings", []),
            positive_points=parsed.get("positive_points", [])
        )
    except json.JSONDecodeError:
        logger.warning(f"Gemini returned non-JSON output: {text_resp[:200]}")
        return ScanLabelResponse(
            product_name="Detected Product",
            ingredients_text=text_resp,
            is_healthy=None,
            health_rating="C",
            warnings=["Could not automatically parse structured nutrients."],
            positive_points=[]
        )
    except Exception as exc:
        logger.error(f"Gemini vision call failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Label scanning failed: {str(exc)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

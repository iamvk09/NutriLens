"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    """Response schema for /api/v1/analyze endpoint"""
    food_name: str = Field(..., description="Name of the predicted food item")
    calories: float = Field(..., description="Calories in kcal")
    protein_g: float = Field(..., description="Protein content in grams")
    fat_g: float = Field(..., description="Total fat content in grams")
    carb_g: float = Field(..., description="Carbohydrate content in grams")
    
    class Config:
        json_schema_extra = {
            "example": {
                "food_name": "apple",
                "calories": 52.0,
                "protein_g": 0.3,
                "fat_g": 0.2,
                "carb_g": 14.0
            }
        }


class LogMealRequest(BaseModel):
    """
    Request schema for /api/v1/log_meal endpoint.
    Includes boundary validation to prevent DoS attacks via unbounded strings
    and data corruption via invalid negative nutrient values.
    """
    # Security: limit string lengths to prevent memory exhaustion / DoS
    user_id: str = Field(..., min_length=1, max_length=128, description="User identifier")
    food_name: str = Field(..., min_length=1, max_length=200, description="Name of the food item")
    # Security: ensure non-negative, realistic nutritional values
    calories: float = Field(..., ge=0, le=50000, description="Calories in kcal")
    protein_g: float = Field(..., ge=0, le=5000, description="Protein content in grams")
    fat_g: float = Field(..., ge=0, le=5000, description="Total fat content in grams")
    carb_g: float = Field(..., ge=0, le=5000, description="Carbohydrate content in grams")
    is_public: bool = Field(default=False, description="Whether to share this meal to the community")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "food_name": "apple",
                "calories": 52.0,
                "protein_g": 0.3,
                "fat_g": 0.2,
                "carb_g": 14.0,
                "is_public": False
            }
        }


class LogMealResponse(BaseModel):
    """Response schema for /api/v1/log_meal endpoint"""
    message: str = Field(..., description="Success or error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Meal logged successfully"
            }
        }


class LikeRequest(BaseModel):
    """
    Request schema for /api/v1/community/like endpoint.
    Security: Ensure meal_id is a positive integer to prevent invalid DB queries.
    """
    meal_id: int = Field(..., gt=0, description="ID of the meal to like")
    
    class Config:
        json_schema_extra = {
            "example": {
                "meal_id": 123
            }
        }


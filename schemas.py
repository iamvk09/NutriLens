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
    """Request schema for /api/v1/log_meal endpoint"""
    user_id: str = Field(..., description="User identifier")
    food_name: str = Field(..., description="Name of the food item")
    calories: float = Field(..., description="Calories in kcal")
    protein_g: float = Field(..., description="Protein content in grams")
    fat_g: float = Field(..., description="Total fat content in grams")
    carb_g: float = Field(..., description="Carbohydrate content in grams")
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
    """Request schema for /api/v1/community/like endpoint"""
    meal_id: int = Field(..., description="ID of the meal to like")
    
    class Config:
        json_schema_extra = {
            "example": {
                "meal_id": 123
            }
        }


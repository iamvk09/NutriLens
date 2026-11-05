"""
Pydantic schemas for request/response validation
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AnalyzeResponse(BaseModel):
    """Response schema for /api/v1/analyze endpoint"""
    food_name: str = Field(..., description="Name of the predicted food item")
    calories: float = Field(..., ge=0, description="Calories in kcal")
    protein_g: float = Field(..., ge=0, description="Protein content in grams")
    fat_g: float = Field(..., ge=0, description="Total fat content in grams")
    carb_g: float = Field(..., ge=0, description="Carbohydrate content in grams")

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
    user_id: Optional[str] = Field(default=None, description="User identifier (overridden by authenticated JWT)")
    food_name: str = Field(..., min_length=1, max_length=100, description="Name of the food item")
    calories: float = Field(..., ge=0, le=10000, description="Calories in kcal")
    protein_g: float = Field(..., ge=0, le=1000, description="Protein content in grams")
    fat_g: float = Field(..., ge=0, le=1000, description="Total fat content in grams")
    carb_g: float = Field(..., ge=0, le=1000, description="Carbohydrate content in grams")
    is_public: bool = Field(default=False, description="Whether to share this meal to the community")

    @field_validator("food_name")
    @classmethod
    def sanitize_food_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("food_name cannot be empty")
        return v

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
    meal_id: Optional[int] = Field(default=None, description="ID of logged meal")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Meal logged successfully",
                "meal_id": 1
            }
        }


class LikeRequest(BaseModel):
    """Request schema for /api/v1/community/like endpoint"""
    meal_id: int = Field(..., gt=0, description="ID of the meal to like")

    class Config:
        json_schema_extra = {
            "example": {
                "meal_id": 123
            }
        }


class ScanLabelResponse(BaseModel):
    """Response schema for /api/v1/scan_label endpoint"""
    product_name: str = Field(default="Unknown Product", description="Product name detected on label")
    ingredients_text: str = Field(default="", description="Ingredients extracted from label")
    is_healthy: Optional[bool] = Field(default=None, description="AI health assessment")
    health_rating: Optional[str] = Field(default=None, description="Health score estimate (A-E)")
    warnings: List[str] = Field(default_factory=list, description="Warnings or problematic ingredients detected")
    positive_points: List[str] = Field(default_factory=list, description="Positive nutritional points")


class BarcodeProductResponse(BaseModel):
    """Response schema for /api/v1/scan_barcode endpoint"""
    barcode: str
    product_name: str
    brand: str
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[int] = None
    ingredients_text: Optional[str] = None
    allergens: Optional[str] = None
    image_url: Optional[str] = None

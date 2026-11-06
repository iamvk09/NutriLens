export interface User {
  id: string;
  email: string;
}

export interface FoodPrediction {
  food_name: string;
  confidence?: number;
  top_predictions?: Array<{ food_name: string; confidence: number }>;
  calories: number;
  protein_g: number;
  fat_g: number;
  carb_g: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  source: 'USDA' | 'FALLBACK_ESTIMATE' | 'OFF' | 'USER_CONFIRMED';
  is_verified: boolean;
}

export interface LoggedMeal {
  id: number;
  user_id: string;
  food_name: string;
  calories: number;
  protein_g: number;
  fat_g: number;
  carb_g: number;
  is_public: boolean;
  likes_count: number;
  created_at: string;
}

export interface ShoppingItem {
  id: number;
  user_id: string;
  item: string;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  score: number;
}

export interface BarcodeProduct {
  barcode: string;
  product_name: string;
  brand: string;
  nutriscore_grade?: string;
  nova_group?: number;
  ingredients_text?: string;
  allergens?: string;
  image_url?: string;
}

export interface LabelAnalysis {
  product_name: string;
  ingredients_text: string;
  is_healthy?: boolean;
  health_rating?: string;
  warnings: string[];
  positive_points: string[];
}

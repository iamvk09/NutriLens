import React, { useState } from 'react';
import { ChefHat, Sparkles, RefreshCw, Plus, Clock, Flame, Apple } from 'lucide-react';
import { supabase } from '../services/supabase';

interface ChefTabProps {
  initialFoodQuery?: string;
  userId: string;
}

export const ChefTab: React.FC<ChefTabProps> = ({
  initialFoodQuery = '',
  userId,
}) => {
  const [foodQuery, setFoodQuery] = useState(initialFoodQuery);
  const [dietaryGoal, setDietaryGoal] = useState<'balanced' | 'high_protein' | 'keto' | 'low_cal'>('balanced');
  const [cookingTime, setCookingTime] = useState<'any' | '15min' | '30min'>('any');
  const [loading, setLoading] = useState(false);
  const [recipe, setRecipe] = useState<{
    title: string;
    description: string;
    prepTime: string;
    calories: number;
    macros: { protein: number; fat: number; carbs: number };
    ingredients: string[];
    steps: string[];
  } | null>(null);

  const handleGenerateRecipe = async () => {
    if (!foodQuery.trim()) return;
    setLoading(true);

    // Simulate smart AI recipe formulation (or API call)
    setTimeout(() => {
      const food = foodQuery.trim();
      const capitalized = food.charAt(0).toUpperCase() + food.slice(1);

      setRecipe({
        title: `${capitalized} Power Bowl with Lemon-Herb Drizzle`,
        description: `A nutrient-packed culinary preparation centering around fresh ${food}, designed to fuel sustained metabolic energy and balanced insulin response.`,
        prepTime: cookingTime === '15min' ? '15 minutes' : '25 minutes',
        calories: dietaryGoal === 'low_cal' ? 320 : dietaryGoal === 'high_protein' ? 480 : 420,
        macros: {
          protein: dietaryGoal === 'high_protein' ? 38 : 24,
          fat: dietaryGoal === 'keto' ? 28 : 12,
          carbs: dietaryGoal === 'keto' ? 8 : 42,
        },
        ingredients: [
          `200g Fresh ${food}`,
          '1 cup Organic Quinoa or Cauliflower Rice',
          '1 tbsp Extra Virgin Cold-Pressed Olive Oil',
          '1/2 Fresh Lemon, squeezed',
          '1 tsp Sea Salt & Smoked Paprika',
          'Fresh Cilantro or Microgreens for garnish',
        ],
        steps: [
          `Wash and cut ${food} into uniform bite-sized pieces.`,
          'Heat olive oil in a non-stick pan over medium heat; lightly sear seasoned ingredients for 6–8 minutes.',
          'Warm the grain base and layer in an artisanal bowl.',
          'Top with the sautéed ingredients, squeeze fresh lemon juice, and garnish with fresh herbs.',
        ],
      });
      setLoading(false);
    }, 700);
  };

  const handleAddIngredientsToShopping = async () => {
    if (!recipe || !recipe.ingredients) return;
    if (supabase) {
      for (const item of recipe.ingredients) {
        await supabase.from('shopping_list').insert({ user_id: userId, item });
      }
      alert('Added all recipe ingredients to your shopping list!');
    } else {
      const saved = JSON.parse(localStorage.getItem(`nutrilens_groceries_${userId}`) || '[]');
      const newItems = recipe.ingredients.map((item, idx) => ({
        id: Date.now() + idx,
        user_id: userId,
        item,
        created_at: new Date().toISOString(),
      }));
      localStorage.setItem(`nutrilens_groceries_${userId}`, JSON.stringify([...newItems, ...saved]));
      alert('Ingredients saved to shopping list!');
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pb-24 md:pb-12 space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">AI Chef & Smart Recipe Creator</h1>
        <p className="text-gray-400 text-sm mt-1">
          Turn recognized foods or pantry items into balanced, chef-grade healthy meals.
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block mb-2">
            Main Ingredient or Food Item
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={foodQuery}
              onChange={(e) => setFoodQuery(e.target.value)}
              placeholder="e.g. Salmon, Tofu, Avocado, Chicken Breast..."
              className="flex-1 bg-[#181d2a] border border-[#272e3d] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition"
            />
            <button
              onClick={handleGenerateRecipe}
              disabled={loading || !foodQuery.trim()}
              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl font-semibold text-sm flex items-center space-x-2 shadow-lg shadow-emerald-600/20 transition flex-shrink-0"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Cooking Recipe...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Recipe</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="text-xs text-gray-400 block mb-1.5 font-medium">Dietary Objective</label>
            <select
              value={dietaryGoal}
              onChange={(e) => setDietaryGoal(e.target.value as any)}
              className="w-full bg-[#181d2a] border border-[#272e3d] rounded-xl px-3 py-2 text-xs text-gray-200 outline-none focus:border-emerald-500"
            >
              <option value="balanced">Balanced Macro Profile</option>
              <option value="high_protein">High Protein (Athletic)</option>
              <option value="keto">Keto / Low Carb</option>
              <option value="low_cal">Caloric Deficit (Weight Loss)</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-400 block mb-1.5 font-medium">Time Availability</label>
            <select
              value={cookingTime}
              onChange={(e) => setCookingTime(e.target.value as any)}
              className="w-full bg-[#181d2a] border border-[#272e3d] rounded-xl px-3 py-2 text-xs text-gray-200 outline-none focus:border-emerald-500"
            >
              <option value="any">Standard Prep (20–30 mins)</option>
              <option value="15min">Quick Prep (&lt;15 mins)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Generated Recipe Card */}
      {recipe && (
        <div className="bg-[#121620] border border-emerald-500/30 rounded-2xl p-6 shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <span className="text-xs uppercase font-bold text-emerald-400 tracking-wider">AI Chef Curated</span>
              <h2 className="text-xl font-bold text-white mt-1">{recipe.title}</h2>
              <p className="text-xs text-gray-400 mt-2 max-w-xl">{recipe.description}</p>
            </div>

            <button
              onClick={handleAddIngredientsToShopping}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#1a2130] hover:bg-[#252d40] text-emerald-400 border border-[#2f384c] transition flex-shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add to Groceries</span>
            </button>
          </div>

          {/* Quick Stats Pill Bar */}
          <div className="flex flex-wrap gap-3 py-3 border-y border-[#222938] text-xs">
            <div className="flex items-center space-x-1.5 text-gray-300">
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
              <span>{recipe.prepTime}</span>
            </div>
            <div className="flex items-center space-x-1.5 text-gray-300">
              <Flame className="w-3.5 h-3.5 text-amber-400" />
              <span>{recipe.calories} kcal</span>
            </div>
            <div className="flex items-center space-x-1.5 text-gray-300">
              <Apple className="w-3.5 h-3.5 text-blue-400" />
              <span>P: {recipe.macros.protein}g | F: {recipe.macros.fat}g | C: {recipe.macros.carbs}g</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Ingredients */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider">Ingredients</h3>
              <ul className="space-y-2 text-xs text-gray-300">
                {recipe.ingredients.map((ing, i) => (
                  <li key={i} className="flex items-center space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>{ing}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Preparation Steps */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider">Instructions</h3>
              <ol className="space-y-3 text-xs text-gray-300">
                {recipe.steps.map((st, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span>{st}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

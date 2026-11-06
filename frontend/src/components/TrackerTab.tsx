import React, { useState, useRef } from 'react';
import { Upload, Camera, Check, AlertCircle, RefreshCw, Sparkles, ChevronRight } from 'lucide-react';
import confetti from 'canvas-confetti';
import { FoodPrediction } from '../types';
import { analyzeFoodImage, logMeal } from '../services/api';

interface TrackerTabProps {
  token: string | null;
  onMealLogged: () => void;
  onCookRecipe: (foodName: string) => void;
}

export const TrackerTab: React.FC<TrackerTabProps> = ({
  token,
  onMealLogged,
  onCookRecipe,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [prediction, setPrediction] = useState<FoodPrediction | null>(null);
  const [customFoodName, setCustomFoodName] = useState('');
  const [portionMultiplier, setPortionMultiplier] = useState(1.0);
  const [isPublic, setIsPublic] = useState(false);
  const [logging, setLogging] = useState(false);
  const [logSuccess, setLogSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setPrediction(null);
      setError(null);
      setLogSuccess(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeFoodImage(selectedFile);
      setPrediction(result);
      setCustomFoodName(result.food_name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()));
    } catch (err: any) {
      setError(err.message || 'Failed to analyze food image. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleLogMeal = async () => {
    if (!prediction && !customFoodName) return;
    setLogging(true);
    setError(null);

    const food = customFoodName.trim() || prediction?.food_name || 'Food Item';
    const cals = Math.round((prediction?.calories || 100) * portionMultiplier * 10) / 10;
    const protein = Math.round((prediction?.protein_g || 2) * portionMultiplier * 10) / 10;
    const fat = Math.round((prediction?.fat_g || 0.5) * portionMultiplier * 10) / 10;
    const carb = Math.round((prediction?.carb_g || 20) * portionMultiplier * 10) / 10;

    try {
      await logMeal(
        {
          food_name: food,
          calories: cals,
          protein_g: protein,
          fat_g: fat,
          carb_g: carb,
          is_public: isPublic,
        },
        token
      );

      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 },
      });

      setLogSuccess(true);
      onMealLogged();
    } catch (err: any) {
      setError(err.message || 'Could not log meal to database.');
    } finally {
      setLogging(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 pb-24 md:pb-12">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">AI Food Recognition & Tracker</h1>
        <p className="text-gray-400 text-sm mt-1">
          Capture or upload your meal photo for instant multi-macro nutritional breakdown.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Image Upload & Preview Card */}
        <div className="lg:col-span-5 space-y-4">
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all min-h-[320px] ${
              previewUrl
                ? 'border-emerald-500/40 bg-[#121620]'
                : 'border-[#272e3d] hover:border-emerald-500/50 bg-[#121620]/60 hover:bg-[#121620]'
            }`}
          >
            {previewUrl ? (
              <div className="w-full flex flex-col items-center">
                <img
                  src={previewUrl}
                  alt="Food snapshot"
                  className="w-full max-h-[260px] object-cover rounded-xl shadow-lg border border-[#272e3d]"
                />
                <p className="text-xs text-gray-400 mt-3 flex items-center">
                  <RefreshCw className="w-3.5 h-3.5 mr-1" /> Click or drop image to replace
                </p>
              </div>
            ) : (
              <div className="text-center space-y-3">
                <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Camera className="w-7 h-7" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-200">Take a photo or upload</p>
                  <p className="text-xs text-gray-400 mt-1">JPEG, PNG, WEBP up to 10MB</p>
                </div>
                <button
                  type="button"
                  className="px-4 py-2 bg-[#1c2230] hover:bg-[#252d40] text-gray-300 text-xs font-medium rounded-lg border border-[#2f384c] transition"
                >
                  Select Photo
                </button>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {selectedFile && !prediction && (
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium rounded-xl shadow-lg shadow-emerald-600/20 flex items-center justify-center space-x-2 transition"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing Food...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Analyze Nutrition</span>
                </>
              )}
            </button>
          )}

          {error && (
            <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-2 text-red-400 text-xs">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Right Column: Nutrition Breakdown & Logging Details */}
        <div className="lg:col-span-7">
          {prediction ? (
            <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 space-y-6 shadow-xl">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    {prediction.source === 'USDA' ? 'USDA Verified Facts' : 'Estimated Nutritional Profile'}
                  </span>
                  <div className="mt-2 flex items-center space-x-2">
                    <input
                      type="text"
                      value={customFoodName}
                      onChange={(e) => setCustomFoodName(e.target.value)}
                      className="text-xl font-bold text-white bg-transparent border-b border-transparent hover:border-gray-500 focus:border-emerald-500 outline-none pb-0.5"
                      title="Click to edit food name"
                    />
                  </div>
                  {prediction.confidence && (
                    <p className="text-xs text-gray-400 mt-1">
                      Recognition Confidence: <span className="text-emerald-400 font-semibold">{Math.round(prediction.confidence * 100)}%</span>
                    </p>
                  )}
                </div>

                <button
                  onClick={() => onCookRecipe(customFoodName)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1a2130] hover:bg-[#252d40] text-emerald-400 border border-[#2f384c] transition"
                >
                  <span>Cook in AI Chef</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Macro Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-[#181d2a] border border-[#242b3b]">
                  <p className="text-[11px] font-medium text-gray-400 uppercase">Calories</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {Math.round((prediction.calories || 0) * portionMultiplier)}
                  </p>
                  <p className="text-[11px] text-gray-500">kcal</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#181d2a] border border-[#242b3b]">
                  <p className="text-[11px] font-medium text-blue-400 uppercase">Protein</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {Math.round((prediction.protein_g || 0) * portionMultiplier * 10) / 10}
                  </p>
                  <p className="text-[11px] text-gray-500">grams</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#181d2a] border border-[#242b3b]">
                  <p className="text-[11px] font-medium text-amber-400 uppercase">Total Fat</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {Math.round((prediction.fat_g || 0) * portionMultiplier * 10) / 10}
                  </p>
                  <p className="text-[11px] text-gray-500">grams</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#181d2a] border border-[#242b3b]">
                  <p className="text-[11px] font-medium text-purple-400 uppercase">Carbs</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {Math.round((prediction.carb_g || 0) * portionMultiplier * 10) / 10}
                  </p>
                  <p className="text-[11px] text-gray-500">grams</p>
                </div>
              </div>

              {/* Portion Multiplier Slider */}
              <div className="space-y-2 pt-2 border-t border-[#222938]">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-medium text-gray-300">Portion Size Multiplier</span>
                  <span className="font-bold text-emerald-400">{portionMultiplier}x</span>
                </div>
                <input
                  type="range"
                  min="0.25"
                  max="3.0"
                  step="0.25"
                  value={portionMultiplier}
                  onChange={(e) => setPortionMultiplier(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-[#222938] rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between text-[10px] text-gray-500">
                  <span>Small (0.5x)</span>
                  <span>Standard (1.0x)</span>
                  <span>Double (2.0x)</span>
                  <span>Feast (3.0x)</span>
                </div>
              </div>

              {/* Share Toggle */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-[#181d2a] border border-[#242b3b]">
                <div>
                  <p className="text-xs font-medium text-gray-200">Share to Community Feed</p>
                  <p className="text-[11px] text-gray-500">Let other members discover and like your meal</p>
                </div>
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-gray-600 bg-gray-700 cursor-pointer"
                />
              </div>

              {/* Log Action Button */}
              {logSuccess ? (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center space-x-2 text-emerald-400 font-medium text-sm">
                  <Check className="w-5 h-5" />
                  <span>Meal Logged Successfully!</span>
                </div>
              ) : (
                <button
                  onClick={handleLogMeal}
                  disabled={logging}
                  className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg shadow-emerald-600/20 flex items-center justify-center space-x-2 transition"
                >
                  {logging ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Saving to History...</span>
                    </>
                  ) : (
                    <span>Log This Meal</span>
                  )}
                </button>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[320px] rounded-2xl border border-dashed border-[#272e3d] bg-[#121620]/30 flex flex-col items-center justify-center p-8 text-center">
              <div className="w-12 h-12 rounded-xl bg-gray-800/50 flex items-center justify-center text-gray-500 mb-3">
                <Upload className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-gray-300">Ready for Recognition</h3>
              <p className="text-xs text-gray-500 mt-1 max-w-sm">
                Upload a photo on the left and tap Analyze to see instant macronutrient breakdown and Food-101 detection.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

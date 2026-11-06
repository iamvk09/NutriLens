import React, { useState, useEffect } from 'react';
import { Heart, Trophy, ChefHat, Sparkles, RefreshCw } from 'lucide-react';
import { LoggedMeal, LeaderboardEntry } from '../types';
import { fetchCommunityFeed, fetchLeaderboard, likeMeal } from '../services/api';

interface CommunityTabProps {
  token: string | null;
  onCookRecipe: (foodName: string) => void;
}

export const CommunityTab: React.FC<CommunityTabProps> = ({
  token,
  onCookRecipe,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'feed' | 'leaderboard'>('feed');
  const [feed, setFeed] = useState<LoggedMeal[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [likedMeals, setLikedMeals] = useState<Record<number, boolean>>({});

  const loadData = async () => {
    setLoading(true);
    try {
      const [feedData, leaderData] = await Promise.all([
        fetchCommunityFeed(),
        fetchLeaderboard(),
      ]);
      setFeed(feedData);
      setLeaderboard(leaderData);
    } catch (err) {
      console.error('Failed to load community data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleLike = async (mealId: number) => {
    if (likedMeals[mealId]) return;
    try {
      const newCount = await likeMeal(mealId, token);
      setLikedMeals((prev) => ({ ...prev, [mealId]: true }));
      setFeed((prev) =>
        prev.map((m) => (m.id === mealId ? { ...m, likes_count: newCount } : m))
      );
    } catch (err: any) {
      if (err.message === 'Already liked') {
        setLikedMeals((prev) => ({ ...prev, [mealId]: true }));
      }
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 pb-24 md:pb-12 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Community Kitchen</h1>
          <p className="text-gray-400 text-sm mt-1">Discover shared recipes, celebrate loggers, and exchange culinary ideas.</p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex bg-[#121620] border border-[#272e3d] rounded-xl p-1 text-xs">
            <button
              onClick={() => setActiveSubTab('feed')}
              className={`px-3.5 py-1.5 rounded-lg font-medium transition ${
                activeSubTab === 'feed'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Public Feed
            </button>
            <button
              onClick={() => setActiveSubTab('leaderboard')}
              className={`px-3.5 py-1.5 rounded-lg font-medium transition ${
                activeSubTab === 'leaderboard'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Weekly Leaderboard
            </button>
          </div>

          <button
            onClick={loadData}
            title="Refresh"
            className="p-2 bg-[#121620] border border-[#272e3d] hover:bg-[#1a2130] text-gray-400 rounded-xl transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {activeSubTab === 'feed' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {feed.length > 0 ? (
            feed.map((meal) => (
              <div
                key={meal.id}
                className="bg-[#121620] border border-[#272e3d] rounded-2xl p-5 flex flex-col justify-between hover:border-emerald-500/40 transition shadow-lg"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-gray-100 text-base line-clamp-1">{meal.food_name}</h3>
                    <span className="text-[10px] text-gray-500">
                      {new Date(meal.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="mt-3 flex items-baseline space-x-2">
                    <span className="text-xl font-extrabold text-emerald-400">{Math.round(meal.calories)}</span>
                    <span className="text-xs text-gray-400">kcal</span>
                  </div>

                  <div className="mt-2 grid grid-cols-3 gap-1 text-[11px] text-gray-400 border-t border-[#222938] pt-2">
                    <div>P: <span className="text-gray-200 font-medium">{Math.round(meal.protein_g)}g</span></div>
                    <div>F: <span className="text-gray-200 font-medium">{Math.round(meal.fat_g)}g</span></div>
                    <div>C: <span className="text-gray-200 font-medium">{Math.round(meal.carb_g)}g</span></div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-[#222938] flex items-center justify-between">
                  <button
                    onClick={() => handleLike(meal.id)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                      likedMeals[meal.id]
                        ? 'text-red-400 bg-red-500/10'
                        : 'text-gray-400 hover:text-red-400 hover:bg-red-500/10'
                    }`}
                  >
                    <Heart className={`w-3.5 h-3.5 ${likedMeals[meal.id] ? 'fill-current' : ''}`} />
                    <span>{meal.likes_count || 0}</span>
                  </button>

                  <button
                    onClick={() => onCookRecipe(meal.food_name)}
                    className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 transition"
                  >
                    <ChefHat className="w-3.5 h-3.5" />
                    <span>AI Chef</span>
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-16 text-center text-gray-500 text-xs">
              No shared meals in the community yet. Be the first to share one when logging in Tracker!
            </div>
          )}
        </div>
      ) : (
        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2">
            <Trophy className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-bold text-white">Top Community Loggers (Last 7 Days)</h2>
          </div>

          <div className="divide-y divide-[#242b3b]">
            {leaderboard.length > 0 ? (
              leaderboard.map((entry) => (
                <div key={entry.rank} className="py-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                        entry.rank === 1
                          ? 'bg-amber-400/20 text-amber-400 border border-amber-400/40'
                          : entry.rank === 2
                          ? 'bg-gray-300/20 text-gray-300 border border-gray-400/40'
                          : entry.rank === 3
                          ? 'bg-amber-700/20 text-amber-600 border border-amber-700/40'
                          : 'bg-[#181d2a] text-gray-400'
                      }`}
                    >
                      #{entry.rank}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-200">
                        {entry.user_id ? entry.user_id.slice(0, 14) + '...' : 'Anonymous Member'}
                      </p>
                      <p className="text-[11px] text-gray-500">Consistent health logger</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-base font-bold text-emerald-400">{entry.score}</span>
                    <span className="text-xs text-gray-400 ml-1">meals</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-gray-500 text-xs">
                No ranking data available for this week.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import { Download, Flame, Dumbbell, Calendar, ArrowUpRight, TrendingUp } from 'lucide-react';
import { LoggedMeal } from '../types';
import { exportHealthPdf } from '../utils/pdfReport';

interface DashboardTabProps {
  meals: LoggedMeal[];
  userEmail: string;
  loading: boolean;
  onRefresh: () => void;
}

export const DashboardTab: React.FC<DashboardTabProps> = ({
  meals,
  userEmail,
  loading,
}) => {
  const [filterPeriod, setFilterPeriod] = useState<'all' | '7d' | '30d'>('all');

  const filteredMeals = React.useMemo(() => {
    if (filterPeriod === 'all') return meals;
    const now = new Date();
    const days = filterPeriod === '7d' ? 7 : 30;
    const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    return meals.filter((m) => new Date(m.created_at) >= cutoff);
  }, [meals, filterPeriod]);

  // Aggregate stats
  const totalMeals = filteredMeals.length;
  const totalCalories = filteredMeals.reduce((acc, m) => acc + (m.calories || 0), 0);
  const totalProtein = filteredMeals.reduce((acc, m) => acc + (m.protein_g || 0), 0);
  const avgCalories = totalMeals > 0 ? Math.round(totalCalories / totalMeals) : 0;
  const avgProtein = totalMeals > 0 ? Math.round((totalProtein / totalMeals) * 10) / 10 : 0;

  // Group by date for simple daily totals
  const dailyCalories = React.useMemo(() => {
    const map: Record<string, number> = {};
    filteredMeals.forEach((m) => {
      const d = new Date(m.created_at).toLocaleDateString();
      map[d] = (map[d] || 0) + m.calories;
    });
    return Object.entries(map).slice(-10); // last 10 dates
  }, [filteredMeals]);

  const maxDailyCal = Math.max(...dailyCalories.map(([, c]) => c), 2000);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 pb-24 md:pb-12 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Nutrition Insights</h1>
          <p className="text-gray-400 text-sm mt-1">Track your progress, macro trends, and health milestones.</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex bg-[#121620] border border-[#272e3d] rounded-xl p-1 text-xs">
            {(['all', '30d', '7d'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setFilterPeriod(period)}
                className={`px-3 py-1.5 rounded-lg font-medium transition ${
                  filterPeriod === period
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {period === 'all' ? 'All Time' : period === '30d' ? '30 Days' : '7 Days'}
              </button>
            ))}
          </div>

          <button
            onClick={() => exportHealthPdf(userEmail, filteredMeals)}
            disabled={totalMeals === 0}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white shadow-lg shadow-emerald-600/20 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Total Meals</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{totalMeals}</p>
          <p className="text-xs text-gray-500 mt-1 flex items-center">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400 mr-1" /> Logged meals in database
          </p>
        </div>

        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Avg Calories</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{avgCalories} <span className="text-sm font-normal text-gray-400">kcal</span></p>
          <p className="text-xs text-gray-500 mt-1">Per logged meal</p>
        </div>

        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Avg Protein</span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Dumbbell className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{avgProtein} <span className="text-sm font-normal text-gray-400">g</span></p>
          <p className="text-xs text-gray-500 mt-1">Daily muscle synthesis target</p>
        </div>

        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Total Energy</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{Math.round(totalCalories)} <span className="text-sm font-normal text-gray-400">kcal</span></p>
          <p className="text-xs text-gray-500 mt-1">Cumulative recorded intake</p>
        </div>
      </div>

      {/* Calorie Trend Chart */}
      <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-4">
        <h3 className="text-sm font-semibold text-gray-200">Daily Caloric Distribution</h3>
        {dailyCalories.length > 0 ? (
          <div className="h-48 flex items-end justify-between gap-2 pt-6">
            {dailyCalories.map(([date, cals], idx) => {
              const heightPct = Math.max(12, Math.round((cals / maxDailyCal) * 100));
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                  <div className="text-[10px] text-gray-400 opacity-0 group-hover:opacity-100 transition">
                    {Math.round(cals)}
                  </div>
                  <div
                    style={{ height: `${heightPct}%` }}
                    className="w-full max-w-[48px] rounded-t-lg bg-gradient-to-t from-emerald-600 to-teal-400 opacity-80 group-hover:opacity-100 transition shadow-sm"
                  />
                  <span className="text-[10px] text-gray-500 truncate w-full text-center">{date.slice(0, 5)}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-12 text-center text-gray-500 text-xs">
            No meal logs recorded for this period. Start logging meals in the Tracker!
          </div>
        )}
      </div>

      {/* Recent Meal History Table */}
      <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-200">Recent Logged Meals</h3>
          <span className="text-xs text-gray-500">{filteredMeals.length} records</span>
        </div>

        {filteredMeals.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#242b3b] text-gray-400 uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3">Food Item</th>
                  <th className="py-3 px-3 text-right">Calories</th>
                  <th className="py-3 px-3 text-right">Protein</th>
                  <th className="py-3 px-3 text-right">Fat</th>
                  <th className="py-3 px-3 text-right">Carbs</th>
                  <th className="py-3 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e2432]">
                {filteredMeals.slice(0, 15).map((meal) => (
                  <tr key={meal.id} className="hover:bg-[#181d2a] transition">
                    <td className="py-3 px-3 text-gray-400 whitespace-nowrap">
                      {new Date(meal.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 font-semibold text-gray-200 whitespace-nowrap">
                      {meal.food_name}
                    </td>
                    <td className="py-3 px-3 text-right text-emerald-400 font-bold whitespace-nowrap">
                      {Math.round(meal.calories)} kcal
                    </td>
                    <td className="py-3 px-3 text-right text-gray-300 whitespace-nowrap">
                      {Math.round(meal.protein_g * 10) / 10}g
                    </td>
                    <td className="py-3 px-3 text-right text-gray-300 whitespace-nowrap">
                      {Math.round(meal.fat_g * 10) / 10}g
                    </td>
                    <td className="py-3 px-3 text-right text-gray-300 whitespace-nowrap">
                      {Math.round(meal.carb_g * 10) / 10}g
                    </td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      {meal.is_public ? (
                        <span className="px-2 py-0.5 text-[9px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
                          Public
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-[9px] font-semibold bg-gray-700/30 text-gray-400 rounded-full">
                          Private
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-gray-500 text-xs">
            {loading ? 'Loading meal records...' : 'No meals found. Snap a photo in Tracker to record your first meal!'}
          </div>
        )}
      </div>
    </div>
  );
};

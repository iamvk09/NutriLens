import React, { useState, useEffect } from 'react';
import { Plus, Trash2, CheckCircle2, ShoppingBag } from 'lucide-react';
import { ShoppingItem } from '../types';
import { supabase } from '../services/supabase';

interface GroceriesTabProps {
  userId: string;
}

export const GroceriesTab: React.FC<GroceriesTabProps> = ({ userId }) => {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [newItemText, setNewItemText] = useState('');
  const [loading, setLoading] = useState(false);

  const loadGroceries = async () => {
    if (!supabase) {
      // Demo fallback in local mode
      const saved = localStorage.getItem(`nutrilens_groceries_${userId}`);
      if (saved) setItems(JSON.parse(saved));
      return;
    }
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('shopping_list')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false });

      if (!error && data) {
        setItems(data);
      }
    } catch (err) {
      console.error('Failed to fetch shopping list', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGroceries();
  }, [userId]);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItemText.trim()) return;

    const trimmed = newItemText.trim();
    setNewItemText('');

    if (!supabase) {
      const newItem: ShoppingItem = {
        id: Date.now(),
        user_id: userId,
        item: trimmed,
        created_at: new Date().toISOString(),
      };
      const updated = [newItem, ...items];
      setItems(updated);
      localStorage.setItem(`nutrilens_groceries_${userId}`, JSON.stringify(updated));
      return;
    }

    try {
      const { data, error } = await supabase
        .from('shopping_list')
        .insert({ user_id: userId, item: trimmed })
        .select()
        .single();

      if (!error && data) {
        setItems((prev) => [data, ...prev]);
      }
    } catch (err) {
      console.error('Failed to insert item', err);
    }
  };

  const handleDeleteItem = async (id: number) => {
    if (!supabase) {
      const updated = items.filter((i) => i.id !== id);
      setItems(updated);
      localStorage.setItem(`nutrilens_groceries_${userId}`, JSON.stringify(updated));
      return;
    }

    try {
      await supabase.from('shopping_list').delete().eq('id', id);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      console.error('Failed to delete item', err);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pb-24 md:pb-12 space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Shopping List</h1>
        <p className="text-gray-400 text-sm mt-1">Organize fresh ingredients and supplies for your meal plans.</p>
      </div>

      {/* Add Item Input Form */}
      <form onSubmit={handleAddItem} className="flex gap-2">
        <input
          type="text"
          value={newItemText}
          onChange={(e) => setNewItemText(e.target.value)}
          placeholder="e.g., Organic spinach, chicken breast, Greek yogurt..."
          className="flex-1 bg-[#121620] border border-[#272e3d] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition"
        />
        <button
          type="submit"
          disabled={!newItemText.trim()}
          className="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl font-semibold text-sm flex items-center space-x-1.5 shadow-lg shadow-emerald-600/20 transition flex-shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Add</span>
        </button>
      </form>

      {/* Items List */}
      <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-[#242b3b]">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Items to Buy</span>
          <span className="text-xs text-gray-500">{items.length} total</span>
        </div>

        {items.length > 0 ? (
          <div className="divide-y divide-[#1e2432]">
            {items.map((item) => (
              <div
                key={item.id}
                className="py-3 px-2 flex items-center justify-between group hover:bg-[#181d2a] rounded-lg transition"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-sm font-medium text-gray-200">{item.item}</span>
                </div>
                <button
                  onClick={() => handleDeleteItem(item.id)}
                  title="Remove item"
                  className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-12 text-center text-gray-500 text-xs space-y-2">
            <ShoppingBag className="w-8 h-8 mx-auto text-gray-600" />
            <p>Your shopping list is clear!</p>
            <p className="text-[11px] text-gray-600">Add food ingredients above or generate them with AI Chef.</p>
          </div>
        )}
      </div>
    </div>
  );
};

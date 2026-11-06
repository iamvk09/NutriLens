import { FoodPrediction, LoggedMeal, LeaderboardEntry, BarcodeProduct, LabelAnalysis } from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_API_URL || '/api/v1';

export async function analyzeFoodImage(file: File): Promise<FoodPrediction> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Analysis failed (${res.status}): ${errorText}`);
  }

  return await res.json();
}

export async function logMeal(
  meal: {
    food_name: string;
    calories: number;
    protein_g: number;
    fat_g: number;
    carb_g: number;
    is_public: boolean;
  },
  token?: string | null
): Promise<{ message: string; meal_id?: number }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/log_meal`, {
    method: 'POST',
    headers,
    body: JSON.stringify(meal),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Meal logging failed: ${err}`);
  }

  return await res.json();
}

export async function fetchUserHistory(userId: string, token?: string | null): Promise<LoggedMeal[]> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/history/${userId}`, {
    headers,
  });

  if (!res.ok) {
    throw new Error(`Failed to load history (${res.status})`);
  }

  return await res.json();
}

export async function fetchCommunityFeed(): Promise<LoggedMeal[]> {
  const res = await fetch(`${API_BASE}/community/feed`);
  if (!res.ok) {
    throw new Error('Failed to load community feed');
  }
  return await res.json();
}

export async function likeMeal(mealId: number, token?: string | null): Promise<number> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/community/like`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ meal_id: mealId }),
  });

  if (res.status === 409) {
    throw new Error('Already liked');
  }
  if (!res.ok) {
    throw new Error('Failed to register like');
  }

  const data = await res.json();
  return data.likes_count;
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  const res = await fetch(`${API_BASE}/community/leaderboard`);
  if (!res.ok) {
    throw new Error('Failed to load leaderboard');
  }
  return await res.json();
}

export async function scanBarcode(file?: File, barcodeNumber?: string): Promise<BarcodeProduct> {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  }
  if (barcodeNumber) {
    formData.append('barcode_number', barcodeNumber);
  }

  const res = await fetch(`${API_BASE}/scan_barcode`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Barcode scan failed: ${err}`);
  }

  return await res.json();
}

export async function scanLabel(file: File): Promise<LabelAnalysis> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/scan_label`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Label inspection failed: ${err}`);
  }

  return await res.json();
}

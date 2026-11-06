import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { TrackerTab } from './components/TrackerTab';
import { DashboardTab } from './components/DashboardTab';
import { CommunityTab } from './components/CommunityTab';
import { GroceriesTab } from './components/GroceriesTab';
import { ChefTab } from './components/ChefTab';
import { ScannerTab } from './components/ScannerTab';
import { AuthModal } from './components/AuthModal';
import { User, LoggedMeal } from './types';
import { fetchUserHistory } from './services/api';
import { supabase } from './services/supabase';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('nutrilens_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('nutrilens_token');
  });

  const [currentTab, setCurrentTab] = useState('tracker');
  const [chefFoodQuery, setChefFoodQuery] = useState('');
  const [userMeals, setUserMeals] = useState<LoggedMeal[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Check Supabase session on mount
  useEffect(() => {
    if (supabase) {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session && session.user) {
          const u = { id: session.user.id, email: session.user.email! };
          setCurrentUser(u);
          setToken(session.access_token);
          localStorage.setItem('nutrilens_user', JSON.stringify(u));
          localStorage.setItem('nutrilens_token', session.access_token);
        }
      });
    }
  }, []);

  const loadMeals = async () => {
    if (!currentUser) return;
    setLoadingHistory(true);
    try {
      const data = await fetchUserHistory(currentUser.id, token);
      setUserMeals(data);
    } catch (err) {
      console.error('Could not load user meals', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadMeals();
    }
  }, [currentUser]);

  const handleAuthSuccess = (user: User, accessToken: string) => {
    setCurrentUser(user);
    setToken(accessToken);
    localStorage.setItem('nutrilens_user', JSON.stringify(user));
    localStorage.setItem('nutrilens_token', accessToken);
  };

  const handleLogout = async () => {
    if (supabase) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.error('Sign out error', err);
      }
    }
    setCurrentUser(null);
    setToken(null);
    localStorage.removeItem('nutrilens_user');
    localStorage.removeItem('nutrilens_token');
  };

  const handleCookInChef = (foodName: string) => {
    setChefFoodQuery(foodName);
    setCurrentTab('chef');
  };

  if (!currentUser) {
    return <AuthModal onSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#0a0c10] text-[#f3f4f6] flex flex-col font-sans selection:bg-emerald-500/30">
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        userEmail={currentUser.email}
        onLogout={handleLogout}
      />

      <main className="flex-1">
        {currentTab === 'tracker' && (
          <TrackerTab
            token={token}
            onMealLogged={loadMeals}
            onCookRecipe={handleCookInChef}
          />
        )}
        {currentTab === 'dashboard' && (
          <DashboardTab
            meals={userMeals}
            userEmail={currentUser.email}
            loading={loadingHistory}
            onRefresh={loadMeals}
          />
        )}
        {currentTab === 'community' && (
          <CommunityTab
            token={token}
            onCookRecipe={handleCookInChef}
          />
        )}
        {currentTab === 'groceries' && (
          <GroceriesTab userId={currentUser.id} />
        )}
        {currentTab === 'chef' && (
          <ChefTab
            initialFoodQuery={chefFoodQuery}
            userId={currentUser.id}
          />
        )}
        {currentTab === 'scanner' && (
          <ScannerTab />
        )}
      </main>
    </div>
  );
}

export default App;

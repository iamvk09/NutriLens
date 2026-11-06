import React from 'react';
import { Camera, BarChart3, ShoppingBag, ChefHat, Users, ScanLine, LogOut, Sparkles } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  userEmail: string;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  userEmail,
  onLogout,
}) => {
  const navItems = [
    { id: 'tracker', label: 'Tracker', icon: Camera },
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'community', label: 'Community', icon: Users },
    { id: 'groceries', label: 'Groceries', icon: ShoppingBag },
    { id: 'chef', label: 'AI Chef', icon: ChefHat },
    { id: 'scanner', label: 'Scanner', icon: ScanLine },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0f131a]/90 backdrop-blur-md border-b border-[#222938]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onSelectTab('tracker')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white">Nutri<span className="text-emerald-400">Lens</span></span>
              <span className="ml-1.5 px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">V2</span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-[#1a2130]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* User profile & actions */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:block text-right">
              <p className="text-xs text-gray-400">Signed in as</p>
              <p className="text-xs font-semibold text-gray-200 truncate max-w-[150px]">{userEmail}</p>
            </div>
            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors border border-transparent hover:border-red-500/20"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#0f131a] border-t border-[#222938] px-2 py-2 z-50">
        <div className="grid grid-cols-6 gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`flex flex-col items-center justify-center py-1.5 rounded-lg text-[11px] font-medium transition-all ${
                  isActive
                    ? 'text-emerald-400 bg-emerald-500/10'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <Icon className="w-4 h-4 mb-0.5" />
                <span className="truncate w-full text-center">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};

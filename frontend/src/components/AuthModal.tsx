import React, { useState } from 'react';
import { Sparkles, Mail, Lock, ArrowRight, ShieldCheck } from 'lucide-react';
import { supabase } from '../services/supabase';

import { User } from '../types';

interface AuthModalProps {
  onSuccess: (user: User, token: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    if (!supabase) {
      // Local Guest demo fallback
      const demoUser = { id: 'demo_user_123', email: email || 'demo@nutrilens.local' };
      onSuccess(demoUser, 'demo_token');
      return;
    }

    try {
      if (mode === 'signup') {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (data.session) {
          onSuccess({ id: data.user!.id, email: data.user!.email! }, data.session.access_token);
        } else {
          setMessage({ type: 'success', text: 'Verification email sent! Check your inbox to confirm.' });
        }
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        if (data.session) {
          onSuccess({ id: data.user.id, email: data.user.email! }, data.session.access_token);
        }
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Authentication failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleGuestEntry = () => {
    onSuccess(
      { id: 'guest_local_user', email: 'guest@nutrilens.local', isGuest: true },
      '' // No token for guest
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a0c10]">
      <div className="w-full max-w-md bg-[#121620] border border-[#272e3d] rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        {/* Decorative ambient gradient */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center space-y-3 mb-8">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome to NutriLens</h1>
          <p className="text-xs text-gray-400">
            AI-driven macronutrient recognition, smart recipes & health tracking.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-[#181d2a] border border-[#272e3d] rounded-xl p-1 mb-6">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setMessage(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
              mode === 'login'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('signup');
              setMessage(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
              mode === 'signup'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-300 block mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@domain.com"
                className="w-full bg-[#181d2a] border border-[#272e3d] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-300 block mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#181d2a] border border-[#272e3d] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>
          </div>

          {message && (
            <div
              className={`p-3 rounded-xl text-xs ${
                message.type === 'error'
                  ? 'bg-red-500/10 border border-red-500/20 text-red-400'
                  : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              }`}
            >
              {message.text}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl text-xs shadow-lg shadow-emerald-600/20 flex items-center justify-center space-x-2 transition"
          >
            <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-[#222938] text-center">
          <button
            type="button"
            onClick={handleGuestEntry}
            className="text-xs font-medium text-gray-400 hover:text-emerald-400 transition flex items-center justify-center space-x-1.5 mx-auto"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Continue as Guest Demo User</span>
          </button>
        </div>
      </div>
    </div>
  );
};

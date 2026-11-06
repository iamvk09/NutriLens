import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://dubspyclplzxjtuwnfxr.supabase.co';
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR1YnNweWNscGx6eGp0dXduZnhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NzQ4ODcsImV4cCI6MjA4MDA1MDg4N30.7lQLKslBBxBtJY7ZTLiVYEfWuk1uFVAABORUyWYi-BI';

export const isSupabaseConfigured = Boolean(
  SUPABASE_URL && 
  SUPABASE_KEY && 
  !SUPABASE_URL.includes('your-project-id') &&
  !SUPABASE_KEY.includes('your-supabase')
);

export const supabase = isSupabaseConfigured 
  ? createClient(SUPABASE_URL, SUPABASE_KEY) 
  : null;

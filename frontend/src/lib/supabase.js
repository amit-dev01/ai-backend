import { createClient } from '@supabase/supabase-js';

const supabaseUrl =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_SUPABASE_URL) ||
  (import.meta.env && import.meta.env.NEXT_PUBLIC_SUPABASE_URL) ||
  (import.meta.env && import.meta.env.VITE_SUPABASE_URL) ||
  'https://xyzcompany.supabase.co';

const supabaseAnonKey =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_SUPABASE_ANON_KEY) ||
  (import.meta.env && import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) ||
  (import.meta.env && import.meta.env.VITE_SUPABASE_ANON_KEY) ||
  'public-anon-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

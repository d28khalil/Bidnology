import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Create Supabase client WITHOUT auth initialization
// This app uses Clerk for authentication, so we disable Supabase's auth to avoid conflicts
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
    storage: undefined, // Disable storage to prevent auth state persistence
  },
  // Disable realtime auth to prevent "Multiple GoTrueClient instances" warning
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
})

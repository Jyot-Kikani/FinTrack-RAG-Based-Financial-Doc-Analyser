// frontend/lib/supabase/client.ts
import { createClient as createSupabaseClient, SupabaseClient } from '@supabase/supabase-js'

let supabaseInstance: SupabaseClient | null = null;

export function createClient() {
  if (typeof window === 'undefined') {
    // For Server-Side Rendering (SSR), always create a new instance
    return createSupabaseClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }

  // For Client-Side Rendering (CSR), act as a singleton to prevent memory leaks and orphaned locks
  if (!supabaseInstance) {
    supabaseInstance = createSupabaseClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  
  return supabaseInstance;
}
import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL    ?? "";
const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabase =
  url && key
    ? createClient(url, key, { auth: { persistSession: false } })
    : null;

export interface WaitlistResult {
  success: boolean;
  error: string | null;
  isDuplicate: boolean;
}

export async function addToWaitlist(
  email: string,
  extras: { newsletter: boolean; research: boolean }
): Promise<WaitlistResult> {
  // No Supabase keys → use server API route
  if (!supabase) {
    try {
      const res  = await fetch("/api/waitlist", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ email, ...extras }),
      });
      const data = await res.json();
      if (res.status === 409) return { success: false, error: "already_registered", isDuplicate: true };
      if (!res.ok)            return { success: false, error: data.error ?? "Server error", isDuplicate: false };
      return { success: true, error: null, isDuplicate: false };
    } catch {
      return { success: false, error: "Network error. Try again.", isDuplicate: false };
    }
  }

  // Direct client insert
  const { error } = await supabase.from("waitlist").insert({
    email:    email.toLowerCase().trim(),
    source:   "friday-v13",
    metadata: { ...extras, timestamp: new Date().toISOString() },
  });

  if (error) {
    const isDuplicate = error.code === "23505";
    return {
      success: false,
      error: isDuplicate ? "already_registered" : error.message,
      isDuplicate,
    };
  }

  return { success: true, error: null, isDuplicate: false };
}

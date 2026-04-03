/**
 * POST /api/waitlist — Server-side email registration
 *
 * Run this SQL once in Supabase SQL Editor before using:
 * ──────────────────────────────────────────────────────
 * CREATE TABLE waitlist (
 *   id         uuid DEFAULT gen_random_uuid() PRIMARY KEY,
 *   email      text UNIQUE NOT NULL,
 *   created_at timestamptz DEFAULT now(),
 *   source     text DEFAULT 'website',
 *   metadata   jsonb DEFAULT '{}'::jsonb
 * );
 * ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;
 * CREATE POLICY "public_insert"  ON waitlist FOR INSERT TO anon WITH CHECK (true);
 * CREATE POLICY "no_public_read" ON waitlist FOR SELECT TO anon USING (false);
 * ──────────────────────────────────────────────────────
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

// Simple in-memory rate limiter (swap for Upstash Redis in production)
const hitMap = new Map<string, number[]>();
function rateLimited(ip: string): boolean {
  const now  = Date.now();
  const hits = (hitMap.get(ip) ?? []).filter((t) => now - t < 60_000);
  hits.push(now);
  hitMap.set(ip, hits);
  return hits.length > 5;
}

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "anon";

  if (rateLimited(ip)) {
    return NextResponse.json({ error: "Too many requests. Wait a minute." }, { status: 429 });
  }

  let body: { email?: string; newsletter?: boolean; research?: boolean };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Bad request." }, { status: 400 });
  }

  const { email, newsletter = true, research = false } = body;

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "Invalid email address." }, { status: 400 });
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // No Supabase in dev → mock success
  if (!supabaseUrl || !supabaseKey) {
    console.log("[waitlist] Mock success:", email);
    return NextResponse.json({ success: true }, { status: 201 });
  }

  const supabase = createClient(supabaseUrl, supabaseKey);
  const { error } = await supabase.from("waitlist").insert({
    email:    email.toLowerCase().trim(),
    source:   "friday-v13-server",
    metadata: { newsletter, research, ip },
  });

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json({ error: "already_registered" }, { status: 409 });
    }
    console.error("[waitlist]", error.message);
    return NextResponse.json({ error: "Server error." }, { status: 500 });
  }

  return NextResponse.json({ success: true }, { status: 201 });
}

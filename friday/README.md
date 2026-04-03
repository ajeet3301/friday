# FRIDAY v13.1 — AI Perception Platform

Fully functional 3D scroll-driven website. Next.js 14 · Three.js · GSAP · Framer Motion · Supabase.

---

## Setup in 4 steps

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment
```bash
cp .env.local.example .env.local
# Open .env.local and paste your Supabase keys
```

### 3. Create Supabase table
Run this SQL once in your Supabase project → SQL Editor:
```sql
CREATE TABLE waitlist (
  id         uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  email      text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now(),
  source     text DEFAULT 'website',
  metadata   jsonb DEFAULT '{}'::jsonb
);
ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_insert"  ON waitlist FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "no_public_read" ON waitlist FOR SELECT TO anon USING (false);
```

### 4. Run locally
```bash
npm run dev
# → http://localhost:3000
```

---

## Deploy to Vercel

```bash
# Push to GitHub first
git init && git add . && git commit -m "feat: FRIDAY v13.1"
git remote add origin https://github.com/YOUR_USER/friday-v13.git
git push -u origin main
```

Then in **Vercel Dashboard → Settings → Environment Variables** add:
```
NEXT_PUBLIC_SUPABASE_URL       = https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY  = eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY      = eyJhbGc...
```

Hit Deploy. Done ✓

---

## Change the site name

One line in `.env.local` or Vercel:
```
NEXT_PUBLIC_APP_NAME="ARIA v2.0"
```

---

## File structure

```
friday-v13/
├── app/
│   ├── globals.css              ← All CSS + CSS variables (dark/light)
│   ├── layout.tsx               ← Root layout, SEO metadata
│   ├── page.tsx                 ← Entry point
│   └── api/waitlist/route.ts   ← Email API + rate limiting
├── components/
│   ├── ThreeScene.tsx           ← Three.js canvas, all 3D models, camera
│   └── Overlay.tsx              ← All HTML: Navbar, sections, form
├── store/
│   └── useTheme.ts              ← Zustand: theme + scroll state
├── lib/
│   └── supabase.ts              ← Supabase client + addToWaitlist()
├── .env.local.example
├── package.json
├── tailwind.config.ts
└── vercel.json
```

---

## What's on each scroll section

| Section | Z-Depth | 3D Object | Content |
|---|---|---|---|
| Hero | z = 0 | Rotating Icosahedron | Title + CTA buttons |
| Audio | z = -15 | 14 orbital spheres | SAM Audio card |
| Vision | z = -30 | Wireframe cube | SAM 3 tracking card |
| Waitlist | z = -45 | Particle ring | Supabase email form |

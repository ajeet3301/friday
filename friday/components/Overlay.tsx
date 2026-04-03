"use client";

/**
 * Overlay.tsx — All HTML content over the 3D canvas
 *
 * Sections:
 *   Hero      (100vh) — title, subtitle, CTA buttons
 *   Audio     (100vh) — SAM Audio card + animated EQ
 *   Vision    (100vh) — SAM 3 tracking card + concept tokens
 *   Waitlist  (100vh) — Supabase email form
 *   Footer             — copyright
 */

import { useState, useEffect, useCallback, CSSProperties } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useThemeStore, SECTIONS } from "@/store/useTheme";
import { addToWaitlist } from "@/lib/supabase";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "FRIDAY v13.1";
const SHORT    = APP_NAME.split(" ")[0];

// ── Helpers ───────────────────────────────────────────────────────────────────

function goTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

// ── Framer variants ───────────────────────────────────────────────────────────

const up = {
  hidden: { opacity: 0, y: 28 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.62, ease: [0.22, 1, 0.36, 1] } },
};
const stagger = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.12 } },
};

// ── Inline style helpers ──────────────────────────────────────────────────────

const S = {
  // Glass card
  card: (maxW = "480px"): CSSProperties => ({
    background:       "var(--glass)",
    backdropFilter:   "blur(24px) saturate(160%)",
    WebkitBackdropFilter: "blur(24px) saturate(160%)",
    border:           "1px solid var(--glass-border)",
    borderRadius:     "16px",
    padding:          "2rem",
    width:            "100%",
    maxWidth:         maxW,
    transition:       "background 0.4s, border-color 0.4s",
  }),

  // Stat box
  stat: (): CSSProperties => ({
    background: "var(--glass)",
    border:     "1px solid var(--glass-border)",
    borderRadius: "10px",
    padding:    "10px 14px",
  }),

  // Tag dot
  dot: (color: string): CSSProperties => ({
    width: "7px", height: "7px", borderRadius: "50%",
    background: color, display: "inline-block",
    boxShadow:  `0 0 8px ${color}`,
  }),
};

// ── Navbar ────────────────────────────────────────────────────────────────────

function Navbar() {
  const { theme, toggleTheme } = useThemeStore();
  const active  = useThemeStore((s) => s.activeSection);
  const [solid, setSolid] = useState(false);

  useEffect(() => {
    const fn = () => setSolid(window.scrollY > 50);
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <nav style={{
      position:  "fixed", top: 0, left: 0, right: 0, zIndex: 100,
      display:   "flex", alignItems: "center", justifyContent: "space-between",
      padding:   "1rem 2rem",
      background: solid ? "var(--navbar)" : "transparent",
      backdropFilter: solid ? "blur(20px)" : "none",
      WebkitBackdropFilter: solid ? "blur(20px)" : "none",
      borderBottom: solid ? "1px solid var(--glass-border)" : "none",
      transition: "background 0.4s, backdrop-filter 0.4s",
    }}>
      {/* Logo mark */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{ width: "26px", height: "26px", position: "relative", borderRadius: "6px", overflow: "hidden" }}>
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, var(--accent), var(--accent2))" }} />
          <div style={{ position: "absolute", inset: "3px", borderRadius: "4px", background: "var(--bg)" }} />
          <div style={{ position: "absolute", inset: "5px", borderRadius: "3px", background: "linear-gradient(135deg, var(--accent), var(--accent2))" }} />
        </div>
        <span style={{ fontSize: "0.88rem", fontWeight: 500, letterSpacing: "0.12em", color: "var(--text)" }}>
          {SHORT}
          <span style={{ color: "var(--text2)", marginLeft: "6px", fontSize: "0.74rem" }}>
            {APP_NAME.replace(SHORT, "").trim()}
          </span>
        </span>
      </div>

      {/* Desktop links */}
      <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
        <div style={{ display: "flex", gap: "1.8rem" }} className="hide-mobile">
          {SECTIONS.map((s, i) => (
            <button key={s.id} onClick={() => goTo(`sec-${i}`)} style={{
              background: "none", border: "none", cursor: "pointer",
              fontSize: "0.72rem", fontWeight: 500, letterSpacing: "0.09em",
              textTransform: "uppercase",
              color: active === i ? "var(--accent)" : "var(--text2)",
              transition: "color 0.2s",
            }}>
              {s.label}
            </button>
          ))}
        </div>

        {/* Theme toggle */}
        <button onClick={toggleTheme} style={{
          background:    "var(--glass)",
          backdropFilter:"blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border:        "1px solid var(--glass-border)",
          borderRadius:  "20px",
          padding:       "0.42rem 1.1rem",
          cursor:        "pointer",
          fontSize:      "0.72rem",
          fontWeight:    500,
          letterSpacing: "0.08em",
          color:         "var(--accent)",
          transition:    "all 0.25s",
        }}>
          {theme === "dark" ? "☀ Light" : "☾ Dark"}
        </button>
      </div>
    </nav>
  );
}

// ── Section dots ──────────────────────────────────────────────────────────────

function Dots() {
  const active = useThemeStore((s) => s.activeSection);
  return (
    <div style={{
      position: "fixed", right: "1.5rem", top: "50%",
      transform: "translateY(-50%)", zIndex: 50,
      display: "flex", flexDirection: "column", gap: "10px",
    }}>
      {SECTIONS.map((s, i) => (
        <button key={s.id} title={s.label} onClick={() => goTo(`sec-${i}`)} style={{
          width:        active === i ? "10px" : "6px",
          height:       active === i ? "10px" : "6px",
          borderRadius: "50%", border: "none", cursor: "pointer", padding: 0,
          background:   active === i ? "var(--accent)" : "var(--text2)",
          opacity:      active === i ? 1 : 0.38,
          boxShadow:    active === i ? "0 0 10px var(--accent)" : "none",
          transition:   "all 0.3s",
        }} />
      ))}
    </div>
  );
}

// ── Section label ─────────────────────────────────────────────────────────────

function Tag({ num, label, color = "var(--accent)" }: { num: string; label: string; color?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "18px" }}>
      <span style={{ fontSize: "0.6rem", letterSpacing: "0.2em", color: "var(--text2)", textTransform: "uppercase" }}>{num}</span>
      <div style={{ height: "1px", width: "26px", background: color, opacity: 0.45 }} />
      <span style={{ fontSize: "0.6rem", letterSpacing: "0.18em", color, textTransform: "uppercase", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
        <span style={S.dot(color)} /> {label}
      </span>
    </div>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section id="sec-0" className="section" style={{ justifyContent: "center", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
      <motion.div variants={stagger} initial="hidden" animate="show" style={{ maxWidth: "640px", margin: "0 auto" }}>

        <motion.p variants={up} style={{
          fontSize: "0.68rem", letterSpacing: "0.34em", textTransform: "uppercase",
          color: "var(--accent)", marginBottom: "1.2rem", fontWeight: 600,
          display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
        }}>
          <span style={{ ...S.dot("var(--accent)"), animation: "pulse 2s infinite" }} />
          Meta Superintelligence Labs
        </motion.p>

        <motion.h1 variants={up} style={{
          fontSize: "clamp(2.8rem, 7vw, 5.5rem)",
          fontWeight: 200, lineHeight: 1.06, letterSpacing: "-0.02em",
          color: "var(--text)", margin: "0 0 1.4rem",
        }}>
          The Future of<br />
          <span className="grad-text" style={{ fontWeight: 400 }}>AI Perception</span><br />
          Is Here
        </motion.h1>

        <motion.p variants={up} style={{
          fontSize: "1rem", lineHeight: 1.76, color: "var(--text2)",
          maxWidth: "420px", margin: "0 auto 2.4rem",
        }}>
          {APP_NAME} unifies SAM 3 object tracking, spatial audio isolation,
          and real-time 3D reconstruction into one seamless platform.
        </motion.p>

        <motion.div variants={up} style={{ display: "flex", gap: "14px", justifyContent: "center", flexWrap: "wrap" }}>
          <button className="grad-btn" onClick={() => goTo("sec-3")} style={{
            padding: "0.78rem 2rem", borderRadius: "10px",
            fontSize: "0.88rem", fontWeight: 500, letterSpacing: "0.05em",
          }}>
            Request Early Access →
          </button>
          <button onClick={() => goTo("sec-1")} style={{
            padding: "0.78rem 2rem", borderRadius: "10px",
            fontSize: "0.88rem", fontWeight: 500, letterSpacing: "0.05em",
            background: "var(--glass)", backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            border: "1px solid var(--glass-border)", color: "var(--text)",
            cursor: "pointer", transition: "all 0.2s",
          }}>
            Explore Features
          </button>
        </motion.div>

        <motion.div variants={up} style={{ marginTop: "4rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", opacity: 0.38 }}>
          <span style={{ fontSize: "0.6rem", letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--text2)" }}>
            Scroll to explore
          </span>
          <motion.div
            style={{ width: "1px", height: "30px", background: "var(--accent)", opacity: 0.7 }}
            animate={{ scaleY: [1, 0.2, 1] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        </motion.div>
      </motion.div>
    </section>
  );
}

// ── Audio ─────────────────────────────────────────────────────────────────────

const EQ = [60, 90, 42, 80, 56, 88, 38, 76, 62, 94, 48, 82];

function Audio() {
  return (
    <section id="sec-1" className="section" style={{ justifyContent: "flex-start" }}>
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: "-120px" }} variants={stagger}>
        <div style={S.card()}>
          <Tag num="02 / 04" label="SAM Audio" />

          <motion.h2 variants={up} style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", fontWeight: 200, letterSpacing: "-0.02em", color: "var(--text)", margin: "0 0 0.75rem" }}>
            Isolate{" "}
            <span className="grad-text" style={{ fontStyle: "italic", fontWeight: 400 }}>Any Sound</span>
          </motion.h2>

          <motion.p variants={up} style={{ fontSize: "0.875rem", lineHeight: 1.76, color: "var(--text2)", margin: "0 0 1.5rem" }}>
            Foundation model for audio separation using text, visual, or temporal prompts.
            Works across speech, music, SFX, and environmental soundscapes.
          </motion.p>

          {/* Animated EQ bars */}
          <motion.div variants={up} style={{ display: "flex", alignItems: "flex-end", gap: "3px", height: "44px", marginBottom: "1.5rem" }}>
            {EQ.map((h, i) => (
              <motion.div key={i} style={{
                flex: 1, borderRadius: "3px", height: `${h}%`,
                background: "linear-gradient(to top, var(--accent), var(--accent2))",
              }}
                animate={{ scaleY: [1, 0.22 + Math.random() * 0.5, 1] }}
                transition={{ duration: 0.78 + i * 0.04, repeat: Infinity, delay: i * 0.065, ease: "easeInOut" }}
              />
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div variants={up} style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "1rem", paddingTop: "1.2rem", borderTop: "1px solid var(--glass-border)" }}>
            {[{ v: "3×", l: "Model sizes" }, { v: "6", l: "Sound categories" }, { v: "98%", l: "Precision score" }].map((s) => (
              <div key={s.l} style={{ textAlign: "center" }}>
                <div className="grad-text" style={{ fontSize: "1.6rem", fontWeight: 300 }}>{s.v}</div>
                <div style={{ fontSize: "0.62rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text2)", marginTop: "4px" }}>{s.l}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}

// ── Vision ────────────────────────────────────────────────────────────────────

const CONCEPTS  = ["person walking", "red car", "coffee cup", "laptop", "glass bottle", "white shirt", "open door", "cat sleeping"];
const METRICS   = [{ l: "Benchmark", v: "SA-Co/Gold" }, { l: "cgF1 Score", v: "54.1" }, { l: "Model Size", v: "848M params" }, { l: "Release", v: "SAM 3.1" }];

function Vision() {
  return (
    <section id="sec-2" className="section" style={{ justifyContent: "flex-end" }}>
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: "-120px" }} variants={stagger}>
        <div style={S.card()}>
          <Tag num="03 / 04" label="SAM 3 Vision" color="var(--accent2)" />

          <motion.h2 variants={up} style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", fontWeight: 200, letterSpacing: "-0.02em", color: "var(--text)", margin: "0 0 0.75rem" }}>
            Track{" "}
            <span className="grad-text" style={{ fontStyle: "italic", fontWeight: 400 }}>Everything</span>
          </motion.h2>

          <motion.p variants={up} style={{ fontSize: "0.875rem", lineHeight: 1.76, color: "var(--text2)", margin: "0 0 1.2rem" }}>
            Open-vocabulary segmentation &amp; tracking across 270K+ unique concepts.
            75–80% human-level performance on the SA-Co benchmark.
          </motion.p>

          {/* Concept tokens */}
          <motion.div variants={up} style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "1.2rem" }}>
            {CONCEPTS.map((c) => (
              <span key={c} style={{
                fontSize: "0.68rem", padding: "3px 10px", borderRadius: "5px",
                border: "1px solid var(--accent2)", color: "var(--accent2)",
                background: "rgba(96,165,250,0.06)", fontFamily: "monospace", letterSpacing: "0.06em",
              }}>
                {c}
              </span>
            ))}
          </motion.div>

          {/* Metrics */}
          <motion.div variants={up} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", paddingTop: "1rem", borderTop: "1px solid var(--glass-border)" }}>
            {METRICS.map((m) => (
              <div key={m.l} style={S.stat()}>
                <div style={{ fontSize: "0.6rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent2)", marginBottom: "4px" }}>{m.l}</div>
                <div style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text)" }}>{m.v}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}

// ── Waitlist ──────────────────────────────────────────────────────────────────

type FS = "idle" | "loading" | "success" | "error" | "duplicate";

function Waitlist() {
  const [email, setEmail]   = useState("");
  const [state, setState]   = useState<FS>("idle");
  const [msg,   setMsg]     = useState("");
  const [news,  setNews]    = useState(true);
  const [res,   setRes]     = useState(false);

  const submit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setState("error"); setMsg("Please enter a valid email address."); return;
    }
    setState("loading");
    const r = await addToWaitlist(email, { newsletter: news, research: res });
    if (r.success)          { setState("success"); setEmail(""); }
    else if (r.isDuplicate) { setState("duplicate"); }
    else                    { setState("error"); setMsg(r.error ?? "Something went wrong."); }
  }, [email, news, res]);

  return (
    <section id="sec-3" className="section" style={{ justifyContent: "center", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: "-100px" }} variants={stagger} style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>

        <motion.p variants={up} style={{ fontSize: "0.68rem", letterSpacing: "0.3em", textTransform: "uppercase", color: "var(--accent)", marginBottom: "1rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ ...S.dot("var(--accent)") }} /> Limited Early Access
        </motion.p>

        <motion.h2 variants={up} style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)", fontWeight: 200, letterSpacing: "-0.02em", color: "var(--text)", margin: "0 0 3rem" }}>
          Be First to <span className="grad-text">Experience</span> {SHORT}
        </motion.h2>

        <motion.div variants={up} style={{ width: "100%", maxWidth: "440px" }}>
          <div style={S.card("440px")}>
            <Tag num="04 / 04" label="Early Access" />

            <AnimatePresence mode="wait">

              {/* ── Success ── */}
              {state === "success" && (
                <motion.div key="ok" initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} style={{ textAlign: "center", padding: "1.5rem 0" }}>
                  <div style={{ width: "58px", height: "58px", borderRadius: "50%", margin: "0 auto 1rem", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#6ee7b7" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 400, color: "var(--text)", margin: "0 0 8px" }}>You&apos;re on the list!</h3>
                  <p style={{ fontSize: "0.875rem", color: "var(--text2)", lineHeight: 1.65, margin: 0 }}>
                    We&apos;ll email you when {SHORT} launches. No spam, ever.
                  </p>
                </motion.div>
              )}

              {/* ── Duplicate ── */}
              {state === "duplicate" && (
                <motion.div key="dup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: "center", padding: "1rem 0" }}>
                  <p style={{ fontSize: "0.9rem", color: "var(--text)", marginBottom: "1rem" }}>
                    Already registered — you&apos;re all set! 🎉
                  </p>
                  <button onClick={() => { setState("idle"); setEmail(""); }} style={{ background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: "0.8rem", textDecoration: "underline" }}>
                    Use a different email
                  </button>
                </motion.div>
              )}

              {/* ── Form ── */}
              {["idle", "loading", "error"].includes(state) && (
                <motion.form key="form" onSubmit={submit} initial={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                  <div>
                    <h3 style={{ fontSize: "1.2rem", fontWeight: 300, color: "var(--text)", margin: "0 0 5px" }}>Get Early Access</h3>
                    <p style={{ fontSize: "0.8rem", color: "var(--text2)", margin: 0 }}>No spam. Unsubscribe anytime.</p>
                  </div>

                  <input
                    type="email" value={email} placeholder="your@email.com"
                    disabled={state === "loading"}
                    onChange={(e) => { setEmail(e.target.value); if (state === "error") setState("idle"); }}
                    style={{
                      width: "100%", padding: "0.78rem 1rem", borderRadius: "10px",
                      fontSize: "0.875rem", outline: "none",
                      background: "var(--glass)", backdropFilter: "blur(12px)",
                      WebkitBackdropFilter: "blur(12px)",
                      border: `1px solid ${state === "error" ? "rgba(239,68,68,0.5)" : "var(--glass-border)"}`,
                      color: "var(--text)", transition: "border-color 0.2s",
                    }}
                  />

                  {/* Preferences */}
                  <div style={{ display: "flex", gap: "1.2rem" }}>
                    {[{ label: "Product updates", v: news, fn: setNews }, { label: "Research papers", v: res, fn: setRes }].map(({ label, v, fn }) => (
                      <label key={label} style={{ display: "flex", alignItems: "center", gap: "7px", cursor: "pointer", fontSize: "0.78rem", color: "var(--text2)" }}>
                        <input type="checkbox" checked={v} onChange={(e) => fn(e.target.checked)} style={{ width: "14px", height: "14px", accentColor: "var(--accent)", cursor: "pointer" }} />
                        {label}
                      </label>
                    ))}
                  </div>

                  {/* Error */}
                  <AnimatePresence>
                    {state === "error" && (
                      <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} style={{ fontSize: "0.78rem", padding: "8px 12px", borderRadius: "8px", color: "#fca5a5", background: "rgba(239,68,68,0.09)", border: "1px solid rgba(239,68,68,0.22)", margin: 0 }}>
                        {msg}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  {/* Submit */}
                  <button type="submit" disabled={state === "loading"} className="grad-btn" style={{
                    padding: "0.82rem", borderRadius: "10px",
                    fontSize: "0.9rem", fontWeight: 500, letterSpacing: "0.04em",
                    opacity: state === "loading" ? 0.7 : 1,
                    cursor: state === "loading" ? "not-allowed" : "pointer",
                  }}>
                    {state === "loading" ? (
                      <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                        <svg className="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="3" strokeOpacity="0.25" />
                          <path d="M22 12a10 10 0 00-10-10" stroke="white" strokeWidth="3" strokeLinecap="round" />
                        </svg>
                        Joining...
                      </span>
                    ) : "Join the Waitlist →"}
                  </button>

                  <p style={{ textAlign: "center", fontSize: "0.65rem", color: "var(--text2)", margin: 0 }}>
                    Powered by Supabase · Encrypted · Zero spam
                  </p>
                </motion.form>
              )}

            </AnimatePresence>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer style={{
      padding: "2rem", textAlign: "center",
      borderTop: "1px solid var(--glass-border)",
      color: "var(--text2)", fontSize: "0.72rem", letterSpacing: "0.08em",
    }}>
      © 2026 {APP_NAME} · Meta Superintelligence Labs · Built on SAM 3
    </footer>
  );
}

// ── Export ────────────────────────────────────────────────────────────────────

export default function Overlay() {
  return (
    <>
      <div id="progress-bar" />
      <Navbar />
      <Dots />

      <div id="overlay">
        <Hero />
        <Audio />
        <Vision />
        <Waitlist />
        <Footer />
      </div>

      <style>{`
        @media (max-width: 640px) { .hide-mobile { display: none !important; } }
      `}</style>
    </>
  );
}

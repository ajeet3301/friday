import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light";

interface ThemeStore {
  theme: Theme;
  scrollProgress: number;
  activeSection: number;
  cameraZ: number;
  toggleTheme: () => void;
  setScrollProgress: (p: number) => void;
  setActiveSection: (i: number) => void;
  setCameraZ: (z: number) => void;
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: "dark",
      scrollProgress: 0,
      activeSection: 0,
      cameraZ: 5,

      toggleTheme: () =>
        set((state) => {
          const next = state.theme === "dark" ? "light" : "dark";
          if (typeof document !== "undefined") {
            document.documentElement.classList.toggle("dark", next === "dark");
          }
          return { theme: next };
        }),

      setScrollProgress: (p) => set({ scrollProgress: p }),
      setActiveSection:  (i) => set({ activeSection: i }),
      setCameraZ:        (z) => set({ cameraZ: z }),
    }),
    {
      name: "friday-theme-v13",
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        if (state && typeof document !== "undefined") {
          document.documentElement.classList.toggle("dark", state.theme === "dark");
        }
      },
    }
  )
);

export const SECTIONS = [
  { id: "hero",     label: "Hero"     },
  { id: "audio",    label: "Audio"    },
  { id: "vision",   label: "Vision"   },
  { id: "waitlist", label: "Waitlist" },
] as const;

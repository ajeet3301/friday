"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import { useThemeStore } from "@/store/useTheme";

// Lazy-load both to avoid SSR issues with WebGL and browser-only APIs
const ThreeScene = dynamic(() => import("@/components/ThreeScene"), { ssr: false, loading: () => null });
const Overlay    = dynamic(() => import("@/components/Overlay"),    { ssr: false });

function ThemeSync() {
  const theme = useThemeStore((s) => s.theme);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);
  return null;
}

export default function Page() {
  return (
    <>
      <ThemeSync />
      {/* Fixed 3D canvas — z-index: 0, pointer-events: none */}
      <ThreeScene />
      {/* Scrollable HTML overlay — z-index: 10 */}
      <Overlay />
    </>
  );
}

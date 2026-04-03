import type { Metadata, Viewport } from "next";
import "./globals.css";

const NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "FRIDAY v13.1";

export const metadata: Metadata = {
  title: {
    default:  `${NAME} — AI Perception Platform`,
    template: `%s | ${NAME}`,
  },
  description:
    "Next-generation AI platform combining SAM 3 vision tracking, " +
    "spatial audio isolation, and real-time 3D reconstruction.",
  keywords: ["AI", "SAM 3", "computer vision", "audio AI", "3D", "Meta AI"],
  openGraph: {
    title:       `${NAME} — AI Perception Platform`,
    description: "Vision. Audio. 3D. One platform.",
    type:        "website",
  },
  twitter: { card: "summary_large_image", title: NAME },
  robots:  { index: true, follow: true },
};

export const viewport: Viewport = {
  width:        "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: dark)",  color: "#06010f" },
    { media: "(prefers-color-scheme: light)", color: "#f8f7ff" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}

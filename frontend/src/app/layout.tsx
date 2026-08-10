import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { GoogleAnalytics } from "@next/third-parties/google";
import { LanguageProvider } from "@/context/LanguageContext";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://corlutravel.com.tr"),
  title: {
    default: "Çorlu Travel | Tur Acentesi & Seyahat Hizmetleri",
    template: "%s | Çorlu Travel",
  },
  description: "Çorlu çıkışlı günübirlik ve konaklamalı tur paketleri, lüks otobüslü seyahatler, canlı koltuk takibi ve güvenli online rezervasyon.",
  keywords: [
    "Çorlu Tur Acentesi",
    "Çorlu Çıkışlı Turlar",
    "Günübirlik Turlar Çorlu",
    "Kapadokya Turu Çorlu",
    "Salda Gölü Pamukkale Turu",
    "Çorlu Travel",
    "Armonitex Seyahat",
  ],
  authors: [{ name: "Çorlu Travel", url: "https://corlutravel.com.tr" }],
  creator: "Çorlu Travel & Armonitex Booking Infrastructure",
  publisher: "Çorlu Travel",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans bg-canvas-token text-main-token selection:bg-teal-500 selection:text-slate-900">
        <LanguageProvider>
          {children}
        </LanguageProvider>

        {process.env.NEXT_PUBLIC_GA_ID && (
          <GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA_ID} />
        )}
      </body>
    </html>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import Logo from "./Logo";

export default function Header() {
  const pathname = usePathname();
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 border-b border-slate-200 backdrop-blur-md text-slate-900 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* LOGO ALANI - Kesin Kısıtlama: 350x100 piksel */}
        <Link href="/" className="flex items-center group transition-transform hover:scale-[1.01]">
          <Logo className="w-[350px] h-[100px]" />
        </Link>

        {/* MENÜ LİNKLERİ, DİL DEĞİŞTİRİCİ VE ACENTE GİRİŞİ */}
        <div className="flex items-center gap-4 sm:gap-6">
          <nav className="flex items-center space-x-1 sm:space-x-4">
            <Link
              href="/turlar"
              className={`px-3 py-2 text-sm font-semibold transition-all rounded-lg ${
                pathname === "/turlar"
                  ? "text-teal-600 bg-teal-50 border border-teal-200 font-bold shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              {t("header.all_tours")}
            </Link>
            <Link
              href="/turlar?tip=gunubirlik"
              className={`px-3 py-2 text-sm font-semibold transition-all rounded-lg ${
                pathname.includes("gunubirlik")
                  ? "text-teal-600 bg-teal-50 border border-teal-200 font-bold shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              {t("header.daily_tours")}
            </Link>
            <Link
              href="/iletisim"
              className={`px-3 py-2 text-sm font-semibold transition-all rounded-lg ${
                pathname === "/iletisim"
                  ? "text-teal-600 bg-teal-50 border border-teal-200 font-bold shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              {t("header.contact")}
            </Link>
          </nav>

          {/* TR / EN Language Switcher */}
          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-bold shadow-sm">
            <button
              onClick={() => setLanguage("tr")}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                language === "tr"
                  ? "bg-teal-500 text-white font-black shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              TR
            </button>
            <button
              onClick={() => setLanguage("en")}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                language === "en"
                  ? "bg-teal-500 text-white font-black shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              EN
            </button>
          </div>

          {/* B2B GİRİŞ BUTONU */}
          <Link
            href="/auth/login"
            className="btn-primary-token"
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
            {t("header.agent_login")}
          </Link>
        </div>
      </div>
    </header>
  );
}

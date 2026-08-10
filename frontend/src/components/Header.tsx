"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import Logo from "./Logo";

export default function Header() {
  const pathname = usePathname();
  const { language, setLanguage, t } = useLanguage();
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinks = [
    { href: "/turlar", label: t("header.all_tours"), active: pathname === "/turlar" },
    {
      href: "/turlar?tip=gunubirlik",
      label: t("header.daily_tours"),
      active: pathname.includes("gunubirlik"),
    },
    { href: "/iletisim", label: t("header.contact"), active: pathname === "/iletisim" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 border-b border-slate-200 backdrop-blur-md text-slate-900 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
        {/* LOGO */}
        <Link href="/" className="flex items-center group transition-transform hover:scale-[1.01] min-w-0">
          <Logo className="w-full max-w-[200px] sm:max-w-[350px] h-[64px] sm:h-[100px]" />
        </Link>

        {/* MASAÜSTÜ MENÜ */}
        <div className="hidden md:flex items-center gap-4 lg:gap-6">
          <nav className="flex items-center space-x-1 lg:space-x-4">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-2 text-sm font-semibold transition-all rounded-lg ${
                  link.active
                    ? "text-teal-600 bg-teal-50 border border-teal-200 font-bold shadow-sm"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* TR / EN Language Switcher */}
          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-bold shadow-sm">
            <button
              onClick={() => setLanguage("tr")}
              className={`px-2.5 py-1.5 rounded-lg transition-all ${
                language === "tr"
                  ? "bg-teal-500 text-white font-black shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              TR
            </button>
            <button
              onClick={() => setLanguage("en")}
              className={`px-2.5 py-1.5 rounded-lg transition-all ${
                language === "en"
                  ? "bg-teal-500 text-white font-black shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              EN
            </button>
          </div>

          {/* B2B GİRİŞ BUTONU */}
          <Link href="/auth/login" className="btn-primary-token">
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
            {t("header.agent_login")}
          </Link>
        </div>

        {/* MOBİL HAMBURGER */}
        <button
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Menü"
          aria-expanded={menuOpen}
          className="md:hidden inline-flex items-center justify-center w-11 h-11 rounded-lg text-slate-700 hover:bg-slate-100 border border-slate-200"
        >
          {menuOpen ? (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* MOBİL MENÜ PANELİ */}
      {menuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white/95 backdrop-blur-md px-4 py-4 space-y-3">
          <nav className="flex flex-col space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className={`px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
                  link.active
                    ? "text-teal-600 bg-teal-50 border border-teal-200 font-bold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-100">
            {/* TR / EN Language Switcher */}
            <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-bold shadow-sm">
              <button
                onClick={() => setLanguage("tr")}
                className={`px-3 py-2 rounded-lg transition-all ${
                  language === "tr"
                    ? "bg-teal-500 text-white font-black shadow-sm"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                TR
              </button>
              <button
                onClick={() => setLanguage("en")}
                className={`px-3 py-2 rounded-lg transition-all ${
                  language === "en"
                    ? "bg-teal-500 text-white font-black shadow-sm"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                EN
              </button>
            </div>

            <Link
              href="/auth/login"
              onClick={() => setMenuOpen(false)}
              className="btn-primary-token w-full justify-center"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              {t("header.agent_login")}
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

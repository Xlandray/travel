"use client";

interface LogoProps {
  className?: string;
}

export default function Logo({ className = "w-full max-w-[350px] h-[100px]" }: LogoProps) {
  return (
    <div
      className={`relative flex items-center justify-between px-3 sm:px-4 py-2 bg-gradient-to-r from-white via-slate-50 to-teal-50/50 text-slate-900 rounded-xl shadow-md border border-slate-200 overflow-hidden select-none ${className}`}
    >
      {/* Decorative Glow */}
      <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-teal-500/20 rounded-full blur-xl pointer-events-none" />

      {/* Brand Icon & Name */}
      <div className="flex items-center gap-2 sm:gap-3 z-10 min-w-0">
        <div className="w-11 h-11 sm:w-14 sm:h-14 shrink-0 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600 shadow-sm">
          <svg
            className="w-6 h-6 sm:w-8 sm:h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 002 2h1.5a2.5 2.5 0 002.5-2.5V14M12 22a10 10 0 100-20 10 10 0 000 20z"
            />
          </svg>
        </div>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-base sm:text-xl font-extrabold tracking-tight text-slate-900 uppercase font-sans truncate">
              ÇORLU<span className="text-teal-600">TRAVEL</span>
            </span>
          </div>
          <span className="text-[10px] sm:text-[11px] font-medium text-slate-500 tracking-wider uppercase mt-0.5 truncate">
            Tur Acentesi &amp; Seyahat Hizmetleri
          </span>
          <span className="text-[8px] sm:text-[9px] font-mono text-teal-600/70 tracking-tighter">
            ARM-TRV-350X100
          </span>
        </div>
      </div>

      {/* 350x100 Badge Indicator */}
      <div className="hidden md:flex flex-col items-end justify-center border-l border-slate-200 pl-3 z-10 shrink-0">
        <span className="text-[10px] font-mono text-teal-700 font-bold bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
          350x100
        </span>
        <span className="text-[8px] text-slate-500 mt-1 uppercase font-semibold">
          Kurumsal Logo
        </span>
      </div>
    </div>
  );
}

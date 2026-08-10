"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      // 1. First try JSON endpoint
      let res = await fetch(`${getApiBase()}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      // 2. If 404 or 405, fallback to /token form endpoint
      if (res.status === 404 || res.status === 405) {
        const body = new URLSearchParams();
        body.append("username", email);
        body.append("password", password);
        res = await fetch(`${getApiBase()}/auth/token`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: body.toString(),
        });
      }

      if (res.ok) {
        const data = await res.json();
        if (typeof window !== "undefined") {
          localStorage.setItem("token", data.access_token);
          localStorage.setItem("access_token", data.access_token);
        }
        const redirect = typeof window !== "undefined"
          ? new URLSearchParams(window.location.search).get("redirect")
          : null;
        router.push(redirect || "/");
      } else {
        const errData = await res.json().catch(() => ({}));
        setErrorMessage(
          errData.detail || "Giriş başarısız. Lütfen e-posta ve şifrenizi kontrol edin."
        );
      }
    } catch {
      setErrorMessage("Sunucuya bağlanılamadı. Lütfen ağ bağlantınızı kontrol edin.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-md mx-auto py-12 px-4">
      <div>
        <h2 className="text-center text-2xl font-extrabold tracking-tight text-main-token">
          Hesabınıza Giriş Yapın
        </h2>
        <p className="text-center text-xs text-slate-400 mt-1">
          Çorlu Travel Acente ve Kullanıcı Portalı
        </p>
      </div>

      <form className="space-y-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl" onSubmit={handleLogin}>
        {errorMessage && (
          <div className="p-3 bg-rose-950/70 border border-rose-500/40 rounded-xl text-rose-300 text-xs flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1">
            E-posta Adresi
          </label>
          <input
            name="email"
            type="email"
            required
            className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-teal-400 transition-colors"
            placeholder="ornek@corlutravel.com"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1">
            Şifre
          </label>
          <input
            name="password"
            type="password"
            required
            className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-teal-400 transition-colors"
            placeholder="••••••••"
          />
        </div>

        <div className="flex items-center justify-between text-xs pt-1">
          <Link href="/auth/register" className="font-semibold text-teal-400 hover:text-teal-300">
            Hesap oluştur
          </Link>
          <Link href="/auth/forgot-password" className="font-semibold text-slate-400 hover:text-slate-300">
            Şifremi unuttum
          </Link>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary-token w-full py-3.5 rounded-xl text-sm font-bold shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <span className="w-4 h-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
              Giriş yapılıyor...
            </>
          ) : (
            "Giriş Yap"
          )}
        </button>
      </form>
    </div>
  );
}

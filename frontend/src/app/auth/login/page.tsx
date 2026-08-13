"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { ApiError, apiFetch, setToken } from "@/lib/api";
import type { AuthToken } from "@/lib/api-types";

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
      const token = await apiFetch<AuthToken>("/auth/login", {
        method: "POST",
        json: { email, password },
      });

      setToken(token.access_token);
      // The admin panel reads a different key from the same origin in dev.
      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", token.access_token);
      }

      const redirect = new URLSearchParams(window.location.search).get("redirect");
      router.push(redirect || "/");
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.detail
          : "Sunucuya bağlanılamadı. Lütfen ağ bağlantınızı kontrol edin.",
      );
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
        <p className="text-center text-xs text-muted-token mt-1">
          Çorlu Travel Acente ve Kullanıcı Portalı
        </p>
      </div>

      <form
        className="space-y-4 card-token bg-surface-token border-token p-6 rounded-2xl shadow-xl"
        onSubmit={handleLogin}
      >
        {errorMessage && (
          <div className="p-3 bg-danger-soft-token border border-danger-token rounded-xl text-danger-token text-xs flex items-center gap-2">
            <svg
              className="w-4 h-4 flex-shrink-0 text-danger-token"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-1">
            E-posta Adresi
          </label>
          <input
            name="email"
            type="email"
            required
            className="input-token"
            placeholder="ornek@corlutravel.com"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-1">
            Şifre
          </label>
          <input
            name="password"
            type="password"
            required
            className="input-token"
            placeholder="••••••••"
          />
        </div>

        <div className="flex items-center justify-between text-xs pt-1">
          <Link
            href="/auth/register"
            className="font-semibold text-brand-token hover:text-primary-hover-token"
          >
            Hesap oluştur
          </Link>
          <Link
            href="/auth/forgot-password"
            className="font-semibold text-subtle-token hover:text-main-token"
          >
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
              <span className="w-4 h-4 rounded-full border-2 border-white-token border-t-transparent animate-spin" />
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

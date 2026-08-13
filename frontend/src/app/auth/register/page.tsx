"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { sendGAEvent } from "@next/third-parties/google";

import { ApiError, apiFetch } from "@/lib/api";
import type { User } from "@/lib/api-types";

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    const formData = new FormData(e.currentTarget);

    // Pydantic UserCreate şeması (email, full_name, password)
    const payload = Object.fromEntries(formData.entries());

    try {
      await apiFetch<User>("/users", { method: "POST", json: payload });

      // API isteği başarılı olduğunda dönüşümü (conversion) Google'a bildir
      sendGAEvent("event", "generate_lead", {
        method: "register_form",
        currency: "TRY",
      });

      router.push("/auth/login");
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError ? error.detail : "Sunucuya bağlanılamadı. Lütfen tekrar deneyin.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-main-token">
          Yeni Hesap Oluştur
        </h2>
      </div>

      <form className="space-y-4" onSubmit={handleRegister}>
        {errorMessage && (
          <div className="p-3 bg-danger-soft-token border border-danger-token rounded-xl text-danger-token text-xs">
            {errorMessage}
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-main-token">Ad Soyad</label>
          <input
            name="full_name"
            type="text"
            required
            className="mt-1 block w-full px-3 py-2 bg-white-token border border-token rounded-md shadow-xs focus:ring-2 focus:ring-[var(--color-primary)] focus:border-[var(--color-primary)] text-sm text-main-token"
            placeholder="Mert Simge"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-main-token">E-posta</label>
          <input
            name="email"
            type="email"
            required
            className="mt-1 block w-full px-3 py-2 bg-white-token border border-token rounded-md shadow-xs focus:ring-2 focus:ring-[var(--color-primary)] focus:border-[var(--color-primary)] text-sm text-main-token"
            placeholder="ornek@armonitex.com"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-main-token">Şifre</label>
          <input
            name="password"
            type="password"
            required
            minLength={12}
            className="mt-1 block w-full px-3 py-2 bg-white-token border border-token rounded-md shadow-xs focus:ring-2 focus:ring-[var(--color-primary)] focus:border-[var(--color-primary)] text-sm text-main-token"
            placeholder="En az 12 karakter"
          />
          <p className="mt-1 text-xs text-muted-token">Şifre en az 12 karakter olmalıdır.</p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary-token w-full justify-center disabled:opacity-50"
        >
          {isLoading ? "Oluşturuluyor..." : "Kayıt Ol"}
        </button>

        <div className="text-center text-sm">
          <Link
            href="/auth/login"
            className="font-semibold text-brand-token hover:text-primary-hover-token"
          >
            Zaten hesabınız var mı? Giriş yapın
          </Link>
        </div>
      </form>
    </div>
  );
}

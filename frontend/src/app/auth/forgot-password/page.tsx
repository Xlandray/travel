"use client";
import { useState } from "react";
import Link from "next/link";

import { apiFetchOr } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;

    try {
      // The endpoint answers the same way whether or not the address is
      // registered, and so does this page — a failure here must not become a
      // way to find out which addresses exist.
      await apiFetchOr(null, "/auth/forgot-password", { method: "POST", json: { email } });
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-main-token">
          Şifre Sıfırlama
        </h2>
        <p className="mt-2 text-center text-sm text-subtle-token">
          E-posta adresinizi girin, size bir sıfırlama bağlantısı gönderelim.
        </p>
      </div>

      {isSubmitted ? (
        <div className="p-4 bg-success-soft-token border border-success-token text-success-token text-sm rounded-lg text-center font-semibold">
          Sıfırlama talimatları e-posta adresinize gönderildi!
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-semibold text-main-token">E-posta Adresi</label>
            <input
              name="email"
              type="email"
              required
              className="mt-1 block w-full px-3 py-2 bg-white-token border border-token rounded-md shadow-xs focus:ring-2 focus:ring-[var(--color-primary)] focus:border-[var(--color-primary)] text-sm text-main-token"
              placeholder="ornek@armonitex.com"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary-token w-full justify-center disabled:opacity-50"
          >
            {isLoading ? "Gönderiliyor..." : "Bağlantı Gönder"}
          </button>
        </form>
      )}

      <div className="text-center text-sm">
        <Link
          href="/auth/login"
          className="font-semibold text-brand-token hover:text-primary-hover-token"
        >
          ← Giriş sayfasına dön
        </Link>
      </div>
    </div>
  );
}

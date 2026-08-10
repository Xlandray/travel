"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleReset = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    const formData = new FormData(e.currentTarget);
    const new_password = formData.get("new_password") as string;
    const confirm_password = formData.get("confirm_password") as string;

    if (new_password !== confirm_password) {
      setErrorMessage("Şifreler birbiriyle eşleşmiyor.");
      setIsLoading(false);
      return;
    }

    if (new_password.length < 12) {
      setErrorMessage("Şifre en az 12 karakter olmalıdır.");
      setIsLoading(false);
      return;
    }

    try {
      const res = await fetch(`${getApiBase()}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password }),
      });

      if (res.ok) {
        setIsSubmitted(true);
      } else {
        const errData = await res.json().catch(() => ({}));
        setErrorMessage(
          errData.detail || "Şifre sıfırlama bağlantısı geçersiz veya süresi dolmuş."
        );
      }
    } catch {
      setErrorMessage("Sunucuya bağlanılamadı. Lütfen ağ bağlantınızı kontrol edin.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="space-y-6 text-center">
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg font-semibold">
          Geçersiz sıfırlama bağlantısı. E-posta kutunuzdaki tam bağlantıyı kullandığınızdan emin olun.
        </div>
        <Link href="/auth/forgot-password" className="font-semibold text-brand-token">
          ← Yeni sıfırlama bağlantısı iste
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-main-token">
          Yeni Şifre Belirleyin
        </h2>
        <p className="mt-2 text-center text-sm text-subtle-token">
          Hesabınız için yeni bir şifre oluşturun.
        </p>
      </div>

      {isSubmitted ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg text-center font-semibold">
          Şifreniz başarıyla güncellendi!
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleReset}>
          {errorMessage && (
            <div className="p-3 bg-rose-50/70 border border-rose-200 rounded-xl text-rose-700 text-xs">
              {errorMessage}
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-main-token">Yeni Şifre</label>
            <input
              name="new_password"
              type="password"
              required
              minLength={12}
              className="mt-1 block w-full px-3 py-2 bg-white-token border border-token rounded-md shadow-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-main-token"
              placeholder="En az 12 karakter"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-main-token">Şifre (Tekrar)</label>
            <input
              name="confirm_password"
              type="password"
              required
              minLength={12}
              className="mt-1 block w-full px-3 py-2 bg-white-token border border-token rounded-md shadow-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-main-token"
              placeholder="Şifrenizi tekrar girin"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary-token w-full justify-center disabled:opacity-50"
          >
            {isLoading ? "Güncelleniyor..." : "Şifreyi Güncelle"}
          </button>
        </form>
      )}

      <div className="text-center text-sm">
        <Link href="/auth/login" className="font-semibold text-brand-token hover:text-blue-700">
          ← Giriş sayfasına dön
        </Link>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="text-center py-10 text-subtle-token">Yükleniyor...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useLanguage } from "@/context/LanguageContext";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

interface MyBooking {
  id: string;
  departure_id: string;
  boarding_point_id: string | null;
  seat_count: number;
  total_price: number;
  status: "pending" | "confirmed" | "cancelled";
  created_at: string;
  tour_title?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  boarding_point_name?: string | null;
  payment_id?: string | null;
  payment_status?: "pending" | "paid" | "failed" | "refunded" | null;
}

const STATUS_TEXT: Record<MyBooking["status"], string> = {
  pending: "Beklemede",
  confirmed: "Onaylandı",
  cancelled: "İptal Edildi",
};

const STATUS_BADGE: Record<MyBooking["status"], string> = {
  pending: "badge-status-pending",
  confirmed: "badge-status-confirmed",
  cancelled: "badge-status-cancelled",
};

const PAYMENT_TEXT: Record<NonNullable<MyBooking["payment_status"]>, string> = {
  pending: "Ödeme Bekliyor",
  paid: "Ödendi",
  failed: "Ödeme Başarısız",
  refunded: "İade Edildi",
};

const PAYMENT_BADGE: Record<NonNullable<MyBooking["payment_status"]>, string> = {
  pending: "badge-status-pending",
  paid: "badge-status-confirmed",
  failed: "badge-status-cancelled",
  refunded: "badge-status-cancelled",
};

function MyBookingsContent() {
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectAfterLogin = searchParams.get("redirect");

  const [bookings, setBookings] = useState<MyBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const getToken = () => (typeof window !== "undefined" ? localStorage.getItem("token") : null);

  const redirectToLogin = useCallback(() => {
    const redirect = redirectAfterLogin || "/profil/rezervasyonlarim";
    router.replace(`/auth/login?redirect=${encodeURIComponent(redirect)}`);
  }, [router, redirectAfterLogin]);

  useEffect(() => {
    let isMounted = true;
    const token = getToken();

    async function loadBookings() {
      if (!token) {
        redirectToLogin();
        return;
      }

      setLoading(true);
      setErrorMessage(null);
      try {
        const res = await fetch(`${getApiBase()}/bookings/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) {
          if (typeof window !== "undefined") localStorage.removeItem("token");
          redirectToLogin();
          return;
        }
        if (!res.ok) {
          if (isMounted) setErrorMessage("Rezervasyonlarınız yüklenirken bir hata oluştu.");
          return;
        }
        const data = await res.json();
        if (isMounted) setBookings(Array.isArray(data) ? data : []);
      } catch {
        if (isMounted) setErrorMessage("Sunucuya bağlanılamadı. Lütfen tekrar deneyin.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadBookings();

    return () => {
      isMounted = false;
    };
  }, [redirectToLogin]);

  const handleCancel = async (id: string) => {
    const token = getToken();
    if (!token) {
      redirectToLogin();
      return;
    }

    setCancellingId(id);
    setErrorMessage(null);
    try {
      const res = await fetch(`${getApiBase()}/bookings/${id}/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        if (typeof window !== "undefined") localStorage.removeItem("token");
        redirectToLogin();
        return;
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setErrorMessage(err.detail || "Rezervasyon iptal edilemedi. Lütfen tekrar deneyin.");
        return;
      }
      const updated = await res.json();
      setBookings((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
    } catch {
      setErrorMessage("Sunucuya bağlanılamadı. İptal işlemi tamamlanamadı.");
    } finally {
      setCancellingId(null);
    }
  };

  const handleSignOutEverywhere = async () => {
    const token = getToken();
    if (!token) {
      redirectToLogin();
      return;
    }

    setSigningOut(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${getApiBase()}/auth/logout-all`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      // 401 means the sessions were already gone, which is the outcome asked
      // for — either way this device's token is no longer worth keeping.
      if (!res.ok && res.status !== 401) {
        setErrorMessage("Oturumlar kapatılamadı. Lütfen tekrar deneyin.");
        return;
      }
      if (typeof window !== "undefined") localStorage.removeItem("token");
      redirectToLogin();
    } catch {
      setErrorMessage("Sunucuya bağlanılamadı. Oturumlar kapatılamadı.");
    } finally {
      setSigningOut(false);
    }
  };

  const formatDate = (value?: string | null) => {
    if (!value) return "—";
    const [year, month, day] = value.slice(0, 10).split("-");
    return `${day}.${month}.${year}`;
  };

  const formatPrice = (value: number) => `${value.toLocaleString("tr-TR")} ₺`;

  return (
    <div className="max-w-6xl mx-auto px-4 py-12 w-full space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-brand-token uppercase tracking-widest">
            {t("booking.modal_subtitle")}
          </span>
          <h1 className="text-3xl font-extrabold text-main-token mt-1">Rezervasyonlarım</h1>
          <p className="text-subtle-token text-sm mt-1">
            Geçmiş ve aktif tur rezervasyonlarınızı buradan takip edebilir ve iptal edebilirsiniz.
          </p>
        </div>

        <div className="sm:text-right">
          <button
            type="button"
            onClick={handleSignOutEverywhere}
            disabled={signingOut}
            className="btn-danger-token text-sm disabled:opacity-50"
          >
            {signingOut ? "Kapatılıyor..." : "Tüm Cihazlarda Oturumu Kapat"}
          </button>
          <p className="text-xs text-muted-token mt-1 max-w-xs">
            Hesabınıza başka bir cihazdan girilmiş olabileceğinden şüpheleniyorsanız kullanın.
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-2">
          <span>{errorMessage}</span>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((n) => (
            <div key={n} className="card-token rounded-2xl p-6 animate-pulse space-y-4">
              <div className="h-5 bg-slate-100 rounded-md w-2/3" />
              <div className="h-4 bg-slate-100 rounded-md w-1/3" />
            </div>
          ))}
        </div>
      ) : bookings.length === 0 ? (
        <div className="card-token rounded-2xl p-12 text-center space-y-4">
          <h2 className="text-lg font-bold text-main-token">Henüz rezervasyonunuz bulunmuyor.</h2>
          <p className="text-subtle-token text-sm">
            Turlarımıza göz atıp beğendiğiniz bir sefere hızlıca rezervasyon oluşturabilirsiniz.
          </p>
          <Link href="/" className="btn-primary-token justify-center">
            Turları Keşfet
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => (
            <div key={booking.id} className="card-token rounded-2xl p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-bold text-main-token">{booking.tour_title}</h2>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold ${STATUS_BADGE[booking.status]}`}
                    >
                      {STATUS_TEXT[booking.status]}
                    </span>
                    {booking.payment_status && (
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold ${PAYMENT_BADGE[booking.payment_status]}`}
                      >
                        {PAYMENT_TEXT[booking.payment_status]}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-subtle-token">
                    <span>
                      Tarih:{" "}
                      <strong className="text-main-token">
                        {formatDate(booking.start_date)} – {formatDate(booking.end_date)}
                      </strong>
                    </span>
                    {booking.boarding_point_name && (
                      <span>
                        Biniş:{" "}
                        <strong className="text-main-token">{booking.boarding_point_name}</strong>
                      </span>
                    )}
                  </div>

                  <div className="text-sm text-subtle-token">
                    {booking.seat_count} kişi ·{" "}
                    <strong className="text-brand-token">{formatPrice(booking.total_price)}</strong>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                  {booking.status === "pending" && (
                    <Link
                      href={`/odeme?booking=${encodeURIComponent(booking.id)}`}
                      className="btn-primary-token justify-center"
                    >
                      Ödemeye Devam Et
                    </Link>
                  )}
                  {booking.status === "pending" && (
                    <button
                      onClick={() => handleCancel(booking.id)}
                      disabled={cancellingId === booking.id}
                      className="btn-danger-token disabled:opacity-50 justify-center"
                    >
                      {cancellingId === booking.id ? "İptal ediliyor..." : "Rezervasyonu İptal Et"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MyBookingsPage() {
  return (
    <div className="min-h-screen bg-canvas-token text-main-token flex flex-col font-sans">
      <Header />
      <main className="flex-1">
        <Suspense
          fallback={<div className="text-center py-20 text-subtle-token">Yükleniyor...</div>}
        >
          <MyBookingsContent />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}

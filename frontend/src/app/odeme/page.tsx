"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useLanguage } from "@/context/LanguageContext";

interface BookingForPayment {
  id: string;
  seat_count: number;
  total_price: number;
  status: "pending" | "confirmed" | "cancelled";
  tour_title?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  boarding_point_name?: string | null;
}

interface PaymentRecord {
  id: string;
  amount: number;
  method: "card" | "transfer";
  status: "pending" | "paid" | "failed" | "refunded";
  transaction_id?: string | null;
}

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

function PaymentContent() {
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingId = searchParams.get("booking");

  const [booking, setBooking] = useState<BookingForPayment | null>(null);
  const [payment, setPayment] = useState<PaymentRecord | null>(null);
  const [cardHolder, setCardHolder] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardExpiry, setCardExpiry] = useState("");
  const [cardCvv, setCardCvv] = useState("");
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const getToken = () => (typeof window !== "undefined" ? localStorage.getItem("token") : null);

  const redirectToLogin = useCallback(() => {
    const redirect = bookingId
      ? `/odeme?booking=${encodeURIComponent(bookingId)}`
      : "/profil/rezervasyonlarim";
    router.replace(`/auth/login?redirect=${encodeURIComponent(redirect)}`);
  }, [router, bookingId]);

  useEffect(() => {
    let isMounted = true;
    const token = getToken();

    async function loadBooking() {
      if (!bookingId) {
        if (isMounted) setErrorMessage("Geçerli bir rezervasyon seçilmedi.");
        setLoading(false);
        return;
      }
      if (!token) {
        redirectToLogin();
        return;
      }

      setLoading(true);
      try {
        const res = await fetch(`${getApiBase()}/bookings/${bookingId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) {
          if (typeof window !== "undefined") localStorage.removeItem("token");
          redirectToLogin();
          return;
        }
        if (!res.ok) {
          if (isMounted) setErrorMessage("Rezervasyon bilgileri yüklenemedi.");
          return;
        }
        const data = await res.json();
        if (isMounted) setBooking(data);
      } catch {
        if (isMounted) setErrorMessage("Sunucuya bağlanılamadı. Lütfen tekrar deneyin.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadBooking();

    return () => {
      isMounted = false;
    };
  }, [bookingId, redirectToLogin]);

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    if (!token) {
      redirectToLogin();
      return;
    }
    if (!booking) return;

    setPaying(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      // 1) Ödemeyi başlat (tutar sunucuda rezervasyondan sabitlenir)
      const createRes = await fetch(`${getApiBase()}/payments/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ booking_id: booking.id, method: "card" }),
      });
      if (createRes.status === 401) {
        if (typeof window !== "undefined") localStorage.removeItem("token");
        redirectToLogin();
        return;
      }
      if (!createRes.ok) {
        const err = await createRes.json().catch(() => ({}));
        setErrorMessage(err.detail || "Ödeme başlatılamadı.");
        return;
      }
      const createdPayment: PaymentRecord = await createRes.json();
      setPayment(createdPayment);

      // 2) Mock kartla öde (rezervasyon CONFIRMED'e geçer)
      const payRes = await fetch(`${getApiBase()}/payments/${createdPayment.id}/pay`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ card_holder: cardHolder, card_number: cardNumber.replace(/\s/g, "") }),
      });
      if (payRes.status === 401) {
        if (typeof window !== "undefined") localStorage.removeItem("token");
        redirectToLogin();
        return;
      }
      if (!payRes.ok) {
        const err = await payRes.json().catch(() => ({}));
        setErrorMessage(err.detail || "Ödeme tamamlanamadı.");
        return;
      }
      const paidPayment: PaymentRecord = await payRes.json();
      setPayment(paidPayment);
      setBooking((prev) => (prev ? { ...prev, status: "confirmed" } : prev));
      setSuccessMessage(
        `Ödemeniz başarıyla alındı! İşlem No: ${paidPayment.transaction_id ?? "-"}`,
      );
      setTimeout(() => {
        router.push("/profil/rezervasyonlarim");
      }, 2500);
    } catch {
      setErrorMessage("Ödeme işlemi sırasında bir hata oluştu.");
    } finally {
      setPaying(false);
    }
  };

  const formatDate = (value?: string | null) => {
    if (!value) return "—";
    const [year, month, day] = value.slice(0, 10).split("-");
    return `${day}.${month}.${year}`;
  };

  const formatPrice = (value: number) => `${value.toLocaleString("tr-TR")} ₺`;

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 w-full space-y-8">
      <div>
        <span className="text-xs font-bold text-brand-token uppercase tracking-widest">
          {t("booking.modal_subtitle")}
        </span>
        <h1 className="text-3xl font-extrabold text-main-token mt-1">Ödeme</h1>
        <p className="text-subtle-token text-sm mt-1">
          Simüle edilmiş kart ödemesi ile rezervasyonunuzu onaylayın. Gerçek bir ücret çekilmez.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-2">
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-sm flex items-center gap-2">
          <span>{successMessage}</span>
        </div>
      )}

      {loading ? (
        <div className="card-token rounded-2xl p-8 animate-pulse space-y-4">
          <div className="h-5 bg-slate-100 rounded-md w-2/3" />
          <div className="h-4 bg-slate-100 rounded-md w-1/3" />
        </div>
      ) : !booking ? (
        <div className="card-token rounded-2xl p-12 text-center space-y-4">
          <h2 className="text-lg font-bold text-main-token">Rezervasyon bulunamadı.</h2>
          <Link href="/profil/rezervasyonlarim" className="btn-primary-token justify-center">
            Rezervasyonlarıma Dön
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* ÖDEME FORMU */}
          <form
            onSubmit={handlePay}
            className="lg:col-span-2 bg-surface-token border-token rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl"
          >
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-2">
                  Kart Üzerindeki İsim
                </label>
                <input
                  type="text"
                  value={cardHolder}
                  onChange={(e) => setCardHolder(e.target.value)}
                  placeholder="AD SOYAD"
                  required
                  className="w-full bg-canvas-token border-token text-main-token rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-token transition-colors placeholder:text-muted-token"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-2">
                  Kart Numarası
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value.replace(/[^\d ]/g, "").slice(0, 19))}
                  placeholder="0000 0000 0000 0000"
                  required
                  pattern="[0-9 ]{16,19}"
                  className="w-full bg-canvas-token border-token text-main-token rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-token transition-colors placeholder:text-muted-token"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-2">
                    Son Kullanma
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={cardExpiry}
                    onChange={(e) => setCardExpiry(e.target.value.replace(/[^\d/]/g, "").slice(0, 5))}
                    placeholder="AA/YY"
                    required
                    pattern="\d{2}/\d{2}"
                    className="w-full bg-canvas-token border-token text-main-token rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-token transition-colors placeholder:text-muted-token"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-2">
                    CVV
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={cardCvv}
                    onChange={(e) => setCardCvv(e.target.value.replace(/[^\d]/g, "").slice(0, 4))}
                    placeholder="123"
                    required
                    pattern="\d{3,4}"
                    className="w-full bg-canvas-token border-token text-main-token rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-token transition-colors placeholder:text-muted-token"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={paying || booking.status !== "pending"}
              className="btn-primary-token w-full py-4 rounded-xl text-base shadow-xl font-extrabold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {paying ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                  Ödeniyor...
                </>
              ) : booking.status === "pending" ? (
                "Ödemeyi Tamamla (Mock)"
              ) : (
                "Ödeme Zaten Alındı"
              )}
            </button>

            <p className="text-xs text-muted-token text-center">
              Bu ödeme bir simülasyondur; hiçbir kart bilgisi saklanmaz veya ücret çekilmez.
            </p>
          </form>

          {/* ÖZET KARTI */}
          <div className="card-token rounded-2xl p-6 space-y-6">
            <h3 className="text-lg font-bold text-main-token border-token border-b pb-3">
              Ödeme Özeti
            </h3>

            <div className="space-y-4 text-sm">
              <div>
                <span className="text-xs text-muted-token uppercase font-bold block">Tur</span>
                <span className="text-base font-bold text-main-token">{booking.tour_title}</span>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <span className="text-xs text-muted-token uppercase font-bold block">Gidiş</span>
                  <span className="text-subtle-token font-semibold">{formatDate(booking.start_date)}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-token uppercase font-bold block">Dönüş</span>
                  <span className="text-subtle-token font-semibold">{formatDate(booking.end_date)}</span>
                </div>
              </div>

              <div className="pt-2 border-token border-t flex items-center justify-between">
                <span className="text-subtle-token">Kişi Sayısı</span>
                <span className="font-bold text-main-token">{booking.seat_count} Kişi</span>
              </div>

              {paying && payment && (
                <div className="pt-2 flex items-center justify-between">
                  <span className="text-subtle-token">İşlem No</span>
                  <span className="font-mono text-xs text-brand-token">
                    {payment.transaction_id ?? "..."}
                  </span>
                </div>
              )}

              <div className="pt-4 border-token border-t flex items-center justify-between text-base">
                <span className="font-bold text-main-token">Ödenecek Tutar</span>
                <span className="text-2xl font-black text-brand-token">
                  {formatPrice(booking.total_price)}
                </span>
              </div>
            </div>

            <div className="p-3 bg-brand-token/10 border border-brand-token/20 rounded-xl text-xs text-brand-token space-y-1">
              <div className="font-bold">🔒 Güvenli Simülasyon</div>
              <div className="text-muted-token">
                Ödeme anında rezervasyonunuz &quot;Onaylandı&quot; durumuna geçer ve koltuklar kesinleşir.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PaymentPage() {
  return (
    <div className="min-h-screen bg-canvas-token text-main-token flex flex-col font-sans">
      <Header />
      <main className="flex-1 flex items-center">
        <Suspense fallback={<div className="text-center py-20 text-muted-token">Yükleniyor...</div>}>
          <PaymentContent />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
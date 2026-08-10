"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useLanguage } from "@/context/LanguageContext";

interface BoardingPoint {
  id: string;
  name: string;
  description?: string;
}

interface DepartureDetails {
  id: string;
  tour_title: string;
  start_date: string;
  end_date: string;
  price: number;
  available_seats: number;
  total_quota: number;
}

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

function CheckoutContent() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();
  const departureId = searchParams.get("departure");
  const router = useRouter();

  const [seatCount, setSeatCount] = useState<number>(1);
  const [boardingPointId, setBoardingPointId] = useState<string>("");
  const [boardingPoints, setBoardingPoints] = useState<BoardingPoint[]>([]);
  const [departure, setDeparture] = useState<DepartureDetails | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [fetching, setFetching] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      // Fetch Boarding Points
      try {
        const bpRes = await fetch(`${getApiBase()}/tours/boarding-points`);
        if (bpRes.ok && isMounted) {
          const bpData = await bpRes.json();
          setBoardingPoints(bpData);
          if (Array.isArray(bpData) && bpData.length > 0) {
            setBoardingPointId(bpData[0].id);
          }
        }
      } catch {
        if (isMounted) {
          const fallbackPoints = [
            { id: "33333333-3333-3333-3333-333333333333", name: "Çorlu Merkez (Heykel Önü)" },
            { id: "44444444-4444-4444-4444-444444444444", name: "Orion AVM Önü Duraklar" },
          ];
          setBoardingPoints(fallbackPoints);
          setBoardingPointId(fallbackPoints[0].id);
        }
      }

      if (isMounted) {
        const fallbackDeparture: DepartureDetails = {
          id: departureId || "55555555-5555-5555-5555-555555555555",
          tour_title: "Kapadokya V.I.P Balon Turu",
          start_date: "2026-09-01",
          end_date: "2026-09-03",
          price: 6500,
          available_seats: 25,
          total_quota: 45,
        };
        setDeparture(fallbackDeparture);
        setFetching(false);
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [departureId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!departureId && !departure?.id) {
      setErrorMessage("Geçerli bir sefer seçilmedi.");
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

      const res = await fetch(`${getApiBase()}/bookings/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          departure_id: departureId || departure?.id,
          seat_count: seatCount,
          boarding_point_id: boardingPointId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessMessage(`Rezervasyonunuz başarıyla kilitlendi! ID: ${data.id.slice(0, 8)}... Durum: PENDING`);
        setTimeout(() => {
          router.push(`/odeme?booking=${encodeURIComponent(data.id)}`);
        }, 1500);
      } else if (res.status === 401) {
        setErrorMessage("Rezervasyon oluşturmak için acente girişi yapmalısınız.");
        setTimeout(() => {
          const redirect = `/checkout?departure=${encodeURIComponent(departureId || "")}&boarding_point=${encodeURIComponent(boardingPointId)}`;
          router.push(`/auth/login?redirect=${encodeURIComponent(redirect)}`);
        }, 1500);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Rezervasyon oluşturulamadı.");
      }
    } catch {
      setErrorMessage("Sunucu bağlantı hatası oluştu.");
    } finally {
      setLoading(false);
    }
  };

  const unitPrice = departure?.price || 6500;
  const totalPrice = unitPrice * seatCount;

  return (
    <div className="max-w-5xl mx-auto px-4 py-12 w-full space-y-8">
      <div>
        <span className="text-xs font-bold text-teal-400 uppercase tracking-widest">
          {t("booking.modal_subtitle")}
        </span>
        <h1 className="text-3xl font-extrabold text-white mt-1">Rezervasyonu Tamamla</h1>
        <p className="text-slate-400 text-sm mt-1">
          Seçtiğiniz sefer için stok kilitleme (with_for_update) ve güvenli biniş noktası seçimi.
        </p>
      </div>

      {fetching ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 animate-pulse h-64" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* REZERVASYON FORMU */}
          <form
            onSubmit={handleSubmit}
            className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl"
          >
            {errorMessage && (
              <div className="p-4 bg-rose-950/60 border border-rose-500/40 rounded-xl text-rose-300 text-sm flex items-center gap-2">
                <svg className="w-5 h-5 flex-shrink-0 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{errorMessage}</span>
              </div>
            )}

            {successMessage && (
              <div className="p-4 bg-emerald-950/60 border border-emerald-500/40 rounded-xl text-emerald-300 text-sm flex items-center gap-2">
                <svg className="w-5 h-5 flex-shrink-0 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>{successMessage}</span>
              </div>
            )}

            {/* Kişi Sayısı Seçimi */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Kaç Kişi Katılacaksınız?
              </label>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                <input
                  type="number"
                  min={1}
                  max={Math.min(10, departure?.available_seats || 10)}
                  value={seatCount}
                  onChange={(e) => setSeatCount(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full sm:w-auto bg-slate-950 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-teal-400 transition-colors"
                />
                <span className="text-xs text-slate-400">
                  (Kalan Stok: <strong className="text-teal-400">{departure?.available_seats}</strong> koltuk)
                </span>
              </div>
            </div>

            {/* Biniş Noktası Seçimi */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Biniş Noktası Seçimi
              </label>
              <select
                value={boardingPointId}
                onChange={(e) => setBoardingPointId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-teal-400 transition-colors"
              >
                {boardingPoints.map((bp) => (
                  <option key={bp.id} value={bp.id}>
                    {bp.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary-token w-full py-4 rounded-xl text-base shadow-xl font-extrabold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                  İşleniyor...
                </>
              ) : (
                "Rezervasyonu Onayla (Stok Kilitler)"
              )}
            </button>
          </form>

          {/* ÖZET KART (SUMMARY CARD) */}
          <div className="card-token rounded-2xl p-6 space-y-6">
            <h3 className="text-lg font-bold text-white border-b border-slate-800 pb-3">
              Sefer Özet Kartı
            </h3>

            <div className="space-y-4 text-sm">
              <div>
                <span className="text-xs text-slate-500 uppercase font-bold block">Seçilen Tur</span>
                <span className="text-base font-bold text-white">{departure?.tour_title}</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <span className="text-xs text-slate-500 uppercase font-bold block">Gidiş Tarihi</span>
                  <span className="text-slate-300 font-semibold">{departure?.start_date}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase font-bold block">Dönüş Tarihi</span>
                  <span className="text-slate-300 font-semibold">{departure?.end_date}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400">Kişi Başı Fiyat</span>
                <span className="font-bold text-white">{unitPrice.toLocaleString("tr-TR")} ₺</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-400">Kişi Sayısı</span>
                <span className="font-bold text-teal-400">{seatCount} Kişi</span>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-base">
                <span className="font-bold text-white">Toplam Tutar</span>
                <span className="text-2xl font-black text-teal-400">
                  {totalPrice.toLocaleString("tr-TR")} ₺
                </span>
              </div>
            </div>

            <div className="p-3 bg-teal-500/10 border border-teal-500/20 rounded-xl text-xs text-teal-300 space-y-1">
              <div className="font-bold">🔒 Çifte Satış (Double-Booking) Koruması</div>
              <div className="text-slate-400">
                Stok kilidi (with_for_update) rezervasyon anında 15 dakika boyunca koltuğunuzu garantiye alır.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <div className="min-h-screen bg-canvas-token text-main-token flex flex-col font-sans">
      <Header />
      <main className="flex-1 flex items-center">
        <Suspense fallback={<div className="text-center py-20 text-slate-400">Yükleniyor...</div>}>
          <CheckoutContent />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}

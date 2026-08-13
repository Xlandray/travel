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

      // Fetch the actual departure and its tour from the API
      try {
        const toursRes = await fetch(`${getApiBase()}/tours`);
        if (toursRes.ok && isMounted) {
          const toursData = await toursRes.json();
          if (Array.isArray(toursData)) {
            for (const tour of toursData) {
              const dep = (tour.departures || []).find((d: { id: string }) => d.id === departureId);
              if (dep) {
                setDeparture({
                  id: dep.id,
                  tour_title: tour.title,
                  start_date: dep.start_date,
                  end_date: dep.end_date,
                  price: dep.price,
                  available_seats: dep.available_seats,
                  total_quota: dep.total_quota,
                });
                break;
              }
            }
          }
        }
      } catch {
        // Fallback below
      }

      if (isMounted) {
        setFetching(false);
        if (!departureId) {
          setErrorMessage("Geçerli bir sefer seçilmedi.");
        }
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
        setSuccessMessage(
          `Rezervasyonunuz başarıyla kilitlendi! ID: ${data.id.slice(0, 8)}... Durum: PENDING`,
        );
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

  const unitPrice = departure?.price ?? 0;
  const totalPrice = unitPrice * seatCount;

  return (
    <div className="max-w-5xl mx-auto px-4 py-12 w-full space-y-8">
      <div>
        <span className="text-xs font-bold text-brand-token uppercase tracking-widest">
          {t("booking.modal_subtitle")}
        </span>
        <h1 className="text-3xl font-extrabold text-main-token mt-1">Rezervasyonu Tamamla</h1>
        <p className="text-subtle-token text-sm mt-1">
          Seçtiğiniz sefer için stok kilitleme (with_for_update) ve güvenli biniş noktası seçimi.
        </p>
      </div>

      {fetching ? (
        <div className="card-token border-token rounded-2xl p-8 animate-pulse h-64" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* REZERVASYON FORMU */}
          <form
            onSubmit={handleSubmit}
            className="lg:col-span-2 card-token bg-surface-token border-token rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl"
          >
            {errorMessage && (
              <div className="p-4 bg-danger-soft-token border border-danger-token rounded-xl text-danger-token text-sm flex items-center gap-2">
                <svg
                  className="w-5 h-5 flex-shrink-0"
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

            {successMessage && (
              <div className="p-4 bg-success-soft-token border border-success-token rounded-xl text-success-token text-sm flex items-center gap-2">
                <svg
                  className="w-5 h-5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span>{successMessage}</span>
              </div>
            )}

            {/* Kişi Sayısı Seçimi */}
            <div>
              <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-2">
                Kaç Kişi Katılacaksınız?
              </label>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                <input
                  type="number"
                  min={1}
                  max={Math.min(10, departure?.available_seats || 10)}
                  value={seatCount}
                  onChange={(e) => setSeatCount(Math.max(1, parseInt(e.target.value) || 1))}
                  className="input-token w-full sm:w-auto"
                />
                <span className="text-xs text-muted-token">
                  (Kalan Stok:{" "}
                  <strong className="text-brand-token">{departure?.available_seats}</strong> koltuk)
                </span>
              </div>
            </div>

            {/* Biniş Noktası Seçimi */}
            <div>
              <label className="block text-xs font-bold text-subtle-token uppercase tracking-wider mb-2">
                Biniş Noktası Seçimi
              </label>
              <select
                value={boardingPointId}
                onChange={(e) => setBoardingPointId(e.target.value)}
                className="input-token"
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
                  <span className="w-4 h-4 rounded-full border-2 border-white-token border-t-transparent animate-spin" />
                  İşleniyor...
                </>
              ) : (
                "Rezervasyonu Onayla (Stok Kilitler)"
              )}
            </button>
          </form>

          {/* ÖZET KART (SUMMARY CARD) */}
          <div className="card-token rounded-2xl p-6 space-y-6">
            <h3 className="text-lg font-bold text-main-token border-b border-token pb-3">
              Sefer Özet Kartı
            </h3>

            <div className="space-y-4 text-sm">
              <div>
                <span className="text-xs text-muted-token uppercase font-bold block">
                  Seçilen Tur
                </span>
                <span className="text-base font-bold text-main-token">{departure?.tour_title}</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <span className="text-xs text-muted-token uppercase font-bold block">
                    Gidiş Tarihi
                  </span>
                  <span className="text-subtle-token font-semibold">{departure?.start_date}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-token uppercase font-bold block">
                    Dönüş Tarihi
                  </span>
                  <span className="text-subtle-token font-semibold">{departure?.end_date}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-token flex items-center justify-between">
                <span className="text-muted-token">Kişi Başı Fiyat</span>
                <span className="font-bold text-main-token">
                  {unitPrice.toLocaleString("tr-TR")} ₺
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-token">Kişi Sayısı</span>
                <span className="font-bold text-brand-token">{seatCount} Kişi</span>
              </div>

              <div className="pt-4 border-t border-token flex items-center justify-between text-base">
                <span className="font-bold text-main-token">Toplam Tutar</span>
                <span className="text-2xl font-black text-brand-token">
                  {totalPrice.toLocaleString("tr-TR")} ₺
                </span>
              </div>
            </div>

            <div className="p-3 bg-brand-teal-soft-token border border-brand-teal-token rounded-xl text-xs space-y-1">
              <div className="font-bold text-brand-token">
                🔒 Çifte Satış (Double-Booking) Koruması
              </div>
              <div className="text-subtle-token">
                Stok kilidi (with_for_update) rezervasyon anında 15 dakika boyunca koltuğunuzu
                garantiye alır.
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
        <Suspense
          fallback={<div className="text-center py-20 text-subtle-token">Yükleniyor...</div>}
        >
          <CheckoutContent />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}

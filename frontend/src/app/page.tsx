"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { TourCard } from "@/components/TourCard";
import { useLanguage } from "@/context/LanguageContext";

interface BoardingPoint {
  id: string;
  name: string;
  description?: string;
}

interface Departure {
  id: string;
  start_date: string;
  end_date: string;
  price: number;
  available_seats: number;
}

interface Category {
  id: string;
  name: string;
  slug: string;
}

interface TourImage {
  id: string;
  url: string;
  sort_order: number;
}

interface Hotel {
  id: string;
  name: string;
  city: string;
  star_rating?: number;
}

interface TourHotel {
  id: string;
  night_order: number;
  hotel: Hotel;
}

interface RouteStop {
  id: string;
  day_number: number;
  title: string;
  description?: string;
  boarding_points: { id: string; name: string }[];
}

interface Tour {
  id: string;
  title: string;
  slug: string;
  description: string;
  days: number;
  nights: number;
  price: number;
  image_url?: string;
  category?: Category | null;
  images?: TourImage[];
  hotels?: TourHotel[];
  route_stops?: RouteStop[];
  departures: Departure[];
  boarding_points: BoardingPoint[];
}

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

const SAMPLE_TOURS: Tour[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    title: "Kapadokya Turu",
    slug: "kapadokya-turu",
    description: "Sıcak hava balonları, peribacaları ve yeraltı şehirleriyle dolu unutulmaz bir deneyim.",
    days: 3,
    nights: 2,
    price: 6500,
    image_url: "https://images.unsplash.com/photo-1641128324972-af3212f0f6bd?auto=format&fit=crop&w=800&q=80",
    departures: [
      {
        id: "55555555-5555-5555-5555-555555555555",
        start_date: "2026-09-01",
        end_date: "2026-09-03",
        price: 6500,
        available_seats: 25,
      },
    ],
    boarding_points: [
      { id: "33333333-3333-3333-3333-333333333333", name: "Çorlu Merkez" },
      { id: "44444444-4444-4444-4444-444444444444", name: "Orion AVM Önü" },
    ],
  },
  {
    id: "22222222-2222-2222-2222-222222222222",
    title: "Salda Gölü ve Pamukkale",
    slug: "salda-golu-ve-pamukkale",
    description: "Türkiye'nin Maldivleri Salda Gölü'nün turkuaz sularında ve bembeyaz travertenlerde harika bir gün.",
    days: 1,
    nights: 0,
    price: 2100,
    image_url: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
    departures: [
      {
        id: "66666666-6666-6666-6666-666666666666",
        start_date: "2026-08-25",
        end_date: "2026-08-25",
        price: 2100,
        available_seats: 18,
      },
    ],
    boarding_points: [
      { id: "33333333-3333-3333-3333-333333333333", name: "Çorlu Merkez" },
      { id: "44444444-4444-4444-4444-444444444444", name: "Orion AVM Önü" },
    ],
  },
];

export default function LandingPage() {
  const { t } = useLanguage();
  const [tours, setTours] = useState<Tour[]>(SAMPLE_TOURS);
  const [boardingPoints, setBoardingPoints] = useState<BoardingPoint[]>([
    { id: "33333333-3333-3333-3333-333333333333", name: "Çorlu Merkez" },
    { id: "44444444-4444-4444-4444-444444444444", name: "Orion AVM Önü" },
  ]);
  const [selectedPoint, setSelectedPoint] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let ignore = false;

    async function initData() {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`${getApiBase()}/tours/boarding-points`, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          const data = await res.json();
          if (!ignore && Array.isArray(data) && data.length > 0) {
            setBoardingPoints(data);
          }
        }
      } catch {
        // Fallback
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`${getApiBase()}/tour-categories`, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          const data = await res.json();
          if (!ignore && Array.isArray(data) && data.length > 0) {
            setCategories(data);
          }
        }
      } catch {
        // Fallback
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`${getApiBase()}/tours`, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          const data = await res.json();
          if (!ignore && Array.isArray(data) && data.length > 0) {
            setTours(data);
          }
        }
      } catch {
        // Fallback
      }
    }

    initData();

    return () => {
      ignore = true;
    };
  }, []);

  const executeTourSearch = async (pointName = "", dateStr = "", categoryId = "") => {
    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);

      const params = new URLSearchParams();
      if (pointName) params.append("boarding_point", pointName);
      if (dateStr) params.append("search_date", dateStr);
      if (categoryId) params.append("category_id", categoryId);

      const url = `${getApiBase()}/tours?${params.toString()}`;
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setTours(data);
        }
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    executeTourSearch(selectedPoint, selectedDate, selectedCategory);
  };

  return (
    <div className="min-h-screen bg-canvas-token text-main-token flex flex-col font-sans selection:bg-teal-500 selection:text-slate-900">
      {/* HEADER */}
      <Header />

      {/* HERO BÖLÜMÜ */}
      <section className="relative min-h-[560px] flex items-center justify-center overflow-hidden bg-gradient-to-b from-slate-50 via-slate-100 to-slate-200 px-4 py-20">
        <div className="absolute inset-0 z-0">
          <Image
            src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1920&q=80"
            alt="Çorlu Travel Hero Background"
            fill
            priority
            className="object-cover opacity-25 filter blur-xs scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-100 via-slate-100/70 to-slate-50/60" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-50 border border-teal-200 backdrop-blur-md shadow-sm">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
            <span className="text-xs font-bold text-teal-600 uppercase tracking-wider">
              {t("hero.badge")}
            </span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
            {t("hero.title_prefix")} <br className="hidden sm:inline" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-teal-500 via-emerald-500 to-teal-600">
              {t("hero.title_highlight")}
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
            {t("hero.subtitle")}
          </p>

          <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs font-semibold text-slate-500">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {t("hero.badge_tracking")}
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {t("hero.badge_points")}
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {t("hero.badge_support")}
            </div>
          </div>
        </div>
      </section>

      {/* ARAMA ÇUBUĞU */}
      <section className="relative z-20 max-w-5xl mx-auto px-4 -mt-16 w-full">
        <form
          onSubmit={handleSearch}
          className="bg-white/90 border border-slate-200 backdrop-blur-xl p-4 sm:p-6 rounded-2xl shadow-xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end"
        >
          <div>
            <label className="block text-xs font-bold text-teal-400 uppercase tracking-wider mb-2">
              {t("search.boarding_point")}
            </label>
            <select
              value={selectedPoint}
              onChange={(e) => setSelectedPoint(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 focus:border-teal-500 text-slate-900 rounded-xl px-4 py-3 text-sm focus:outline-none transition-colors"
            >
              <option value="">{t("search.all_points")}</option>
              {boardingPoints.map((bp) => (
                <option key={bp.id} value={bp.name}>
                  {bp.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-teal-400 uppercase tracking-wider mb-2">
              {t("search.category")}
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 focus:border-teal-500 text-slate-900 rounded-xl px-4 py-3 text-sm focus:outline-none transition-colors"
            >
              <option value="">{t("search.all_categories")}</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-teal-400 uppercase tracking-wider mb-2">
              {t("search.date")}
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 focus:border-teal-500 text-slate-900 rounded-xl px-4 py-3 text-sm focus:outline-none transition-colors"
            />
          </div>

          <div>
            <button
              type="submit"
              className="btn-primary-token w-full py-3 px-6 rounded-xl flex items-center justify-center gap-2 transform active:scale-95"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {t("search.button")}
            </button>
          </div>
        </form>
      </section>

      {/* POPÜLER TURLAR BÖLÜMÜ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 w-full">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-12 gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-teal-400">
              {t("tours.category_badge")}
            </span>
            <h2 className="text-3xl font-extrabold text-main-token mt-1">{t("tours.title")}</h2>
            <p className="text-subtle-token text-sm mt-1">{t("tours.subtitle")}</p>
          </div>
          <button
            onClick={() => {
              setSelectedCategory("");
              executeTourSearch("", "", "");
            }}
            className="text-xs font-semibold text-teal-600 hover:text-teal-500 transition-colors flex items-center gap-1 underline underline-offset-4"
          >
            {t("tours.clear_filters")}
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2].map((n) => (
              <div key={n} className="bg-white border border-slate-200 rounded-2xl p-6 animate-pulse space-y-4 shadow-sm">
                <div className="h-48 bg-slate-200 rounded-xl" />
                <div className="h-6 bg-slate-200 rounded w-3/4" />
                <div className="h-4 bg-slate-200 rounded w-full" />
              </div>
            ))}
          </div>
        ) : tours.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3 shadow-sm">
            <h3 className="text-lg font-bold text-slate-800">{t("tours.not_found")}</h3>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {tours.map((tour) => (
              <TourCard key={tour.id} tour={tour} />
            ))}
          </div>
        )}
      </section>

      {/* FOOTER */}
      <Footer />
    </div>
  );
}

import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { TourBookingPanel } from "@/components/TourBookingPanel";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

interface Hotel {
  id: string;
  name: string;
  slug: string;
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

interface TourDetail {
  id: string;
  title: string;
  slug: string;
  description: string;
  days: number;
  nights: number;
  price: number;
  image_url?: string;
  images?: { id: string; url: string; sort_order: number }[];
  hotels?: TourHotel[];
  route_stops?: RouteStop[];
  departures: {
    id: string;
    start_date: string;
    end_date: string;
    price: number;
    available_seats: number;
  }[];
  boarding_points: { id: string; name: string }[];
}

async function fetchTour(slug: string): Promise<TourDetail | null> {
  try {
    const res = await fetch(`${getApiBase()}/tours/${slug}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as TourDetail;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const tour = await fetchTour(slug);
  if (!tour) return { title: "Tur Bulunamadı" };
  return {
    title: `${tour.title} | Çorlu Travel`,
    description: tour.description,
    alternates: { canonical: `/turlar/${tour.slug}` },
  };
}

export default async function TourDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const tour = await fetchTour(slug);
  if (!tour) notFound();

  const photos = [tour.image_url, ...(tour.images ?? []).map((img) => img.url)].filter(
    (url): url is string => Boolean(url),
  );
  const gallery = photos.length > 0 ? [...new Set(photos)] : [];
  const sortedStops = [...(tour.route_stops ?? [])].sort((a, b) => a.day_number - b.day_number);
  const sortedHotels = [...(tour.hotels ?? [])].sort((a, b) => a.night_order - b.night_order);

  return (
    <div className="min-h-screen bg-canvas-token text-main-token flex flex-col font-sans">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        <Link
          href="/"
          className="text-sm text-slate-500 hover:text-teal-600 transition-colors mb-6 inline-block"
        >
          ← Geri Dön
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* LEFT: Gallery + Info */}
          <div className="lg:col-span-2 space-y-8">
            <div className="card-token rounded-2xl overflow-hidden">
              {gallery.length > 0 ? (
                <Image
                  src={gallery[0]}
                  alt={tour.title}
                  width={1600}
                  height={900}
                  className="w-full h-[320px] sm:h-[420px] object-cover"
                />
              ) : (
                <div className="h-[320px] sm:h-[420px] bg-slate-100 flex items-center justify-center text-slate-400 text-sm">
                  Görsel bulunmuyor
                </div>
              )}
              {gallery.length > 1 && (
                <div className="grid grid-cols-4 gap-2 p-3">
                  {gallery.slice(1, 5).map((url) => (
                    <Image
                      key={url}
                      src={url}
                      alt=""
                      width={400}
                      height={300}
                      className="w-full h-24 object-cover rounded-xl"
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="card-token rounded-2xl p-6">
              <span className="text-xs font-bold uppercase tracking-widest text-teal-500">
                {tour.days > 1 ? `${tour.days} Gün ${tour.nights} Gece` : "Günübirlik"}
              </span>
              <h1 className="text-3xl font-black text-main-token mt-1">{tour.title}</h1>
              <p className="text-subtle-token text-sm mt-4 leading-relaxed">{tour.description}</p>

              <div className="flex flex-wrap gap-3 mt-5 pt-5 border-t border-slate-100">
                <span className="px-3 py-1.5 bg-teal-50 text-teal-700 border border-teal-200 rounded-xl text-xs font-bold">
                  {tour.days > 1 ? `${tour.days} Gün · ${tour.nights} Gece` : "Günübirlik"}
                </span>
                {tour.boarding_points.length > 0 && (
                  <span className="px-3 py-1.5 bg-slate-50 text-slate-600 border border-slate-200 rounded-xl text-xs font-bold">
                    Kalkış: {tour.boarding_points.map((bp) => bp.name).join(", ")}
                  </span>
                )}
                {sortedHotels.length > 0 && (
                  <span className="px-3 py-1.5 bg-slate-50 text-slate-600 border border-slate-200 rounded-xl text-xs font-bold">
                    Konaklama: {sortedHotels.map((th) => th.hotel.name).join(", ")}
                  </span>
                )}
              </div>
            </div>

            {sortedStops.length > 0 && (
              <div className="card-token rounded-2xl p-6">
                <h2 className="text-xl font-extrabold text-main-token mb-4">Gün Programı</h2>
                <div className="space-y-4">
                  {sortedStops.map((rs) => (
                    <div key={rs.id} className="border-l-2 border-teal-400 pl-4 py-1">
                      <p className="text-sm font-bold text-slate-800">
                        {rs.day_number}. Gün · {rs.title}
                      </p>
                      {rs.description ? (
                        <p className="text-sm text-slate-500 mt-0.5 leading-relaxed">
                          {rs.description}
                        </p>
                      ) : null}
                      {rs.boarding_points.length > 0 && (
                        <p className="text-xs text-teal-600 mt-1">
                          Biniş: {rs.boarding_points.map((bp) => bp.name).join(", ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {sortedHotels.length > 0 && (
              <div className="card-token rounded-2xl p-6">
                <h2 className="text-xl font-extrabold text-main-token mb-4">Konaklama</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {sortedHotels.map((th) => (
                    <Link
                      key={th.id}
                      href={`/oteller/${th.hotel.slug}`}
                      className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 hover:border-teal-300 hover:bg-teal-50 transition-colors block"
                    >
                      <p className="text-sm font-bold text-slate-800">
                        {th.hotel.star_rating ? `${th.hotel.star_rating}★ ` : ""}
                        {th.hotel.name}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {th.hotel.city} · {th.night_order}. gece
                      </p>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Booking Panel */}
          <div className="lg:sticky lg:top-24 h-fit">
            <TourBookingPanel departures={tour.departures} boardingPoints={tour.boarding_points} />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

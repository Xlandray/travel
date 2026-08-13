import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { TourCard, type GalleryTour } from "@/components/TourCard";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
  }
  return "http://api:8000/api/v1";
};

interface HotelDetail {
  id: string;
  name: string;
  slug: string;
  city: string;
  address?: string | null;
  phone?: string | null;
  star_rating?: number | null;
  description?: string | null;
  image_url?: string | null;
}

const FALLBACK_HOTEL_IMAGE =
  "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=1200&q=80";

async function fetchHotel(slug: string): Promise<HotelDetail | null> {
  try {
    const res = await fetch(`${getApiBase()}/hotels/${slug}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as HotelDetail;
  } catch {
    return null;
  }
}

async function fetchHotelTours(slug: string): Promise<GalleryTour[]> {
  try {
    const res = await fetch(`${getApiBase()}/hotels/${slug}/tours`, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()) as GalleryTour[];
  } catch {
    return [];
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const hotel = await fetchHotel(slug);
  if (!hotel) return { title: "Otel Bulunamadı" };
  return {
    title: `${hotel.name} | Çorlu Travel`,
    description: hotel.description || `${hotel.city} konaklama oteli`,
    alternates: { canonical: `/oteller/${hotel.slug}` },
  };
}

export default async function HotelDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [hotel, tours] = await Promise.all([fetchHotel(slug), fetchHotelTours(slug)]);
  if (!hotel) notFound();

  const image = hotel.image_url || FALLBACK_HOTEL_IMAGE;

  return (
    <div className="min-h-screen bg-canvas-token text-main-token flex flex-col font-sans">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        <Link
          href="/"
          className="text-sm text-subtle-token hover:text-brand-token transition-colors mb-6 inline-block"
        >
          ← Geri Dön
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* LEFT: Gallery + Info */}
          <div className="lg:col-span-2 space-y-8">
            <div className="card-token rounded-2xl overflow-hidden">
              <Image
                src={image}
                alt={hotel.name}
                width={1600}
                height={900}
                className="w-full h-[320px] sm:h-[420px] object-cover"
              />
            </div>

            <div className="card-token rounded-2xl p-6">
              <span className="text-xs font-bold uppercase tracking-widest text-brand-token">
                {hotel.city}
                {hotel.star_rating ? ` · ${hotel.star_rating} Yıldız` : ""}
              </span>
              <h1 className="text-3xl font-black text-main-token mt-1">
                {hotel.star_rating ? `${"★".repeat(hotel.star_rating)} ` : ""}
                {hotel.name}
              </h1>
              <p className="text-subtle-token text-sm mt-4 leading-relaxed">
                {hotel.description || "Bu otel hakkında henüz açıklama eklenmedi."}
              </p>

              <div className="flex flex-wrap gap-3 mt-5 pt-5 border-t border-token">
                {hotel.city && (
                  <span className="px-3 py-1.5 bg-brand-teal-soft-token text-brand-token border border-brand-teal-token rounded-xl text-xs font-bold">
                    📍 {hotel.city}
                  </span>
                )}
                {hotel.phone && (
                  <a
                    href={`tel:${hotel.phone}`}
                    className="px-3 py-1.5 bg-surface-token text-main-token border border-token rounded-xl text-xs font-bold hover:border-brand-teal-token transition-colors"
                  >
                    📞 {hotel.phone}
                  </a>
                )}
              </div>

              {hotel.address && (
                <p className="text-xs text-subtle-token mt-4 leading-relaxed">
                  {hotel.address}
                </p>
              )}
            </div>
          </div>

          {/* RIGHT: Quick facts */}
          <div className="lg:sticky lg:top-24 h-fit">
            <div className="card-token rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-extrabold text-main-token">Otel Bilgileri</h2>
              <div className="space-y-2 text-sm">
                {hotel.star_rating ? (
                  <div className="flex justify-between border-b border-token pb-2">
                    <span className="text-subtle-token">Yıldız</span>
                    <span className="font-bold text-main-token">{hotel.star_rating} ★</span>
                  </div>
                ) : null}
                <div className="flex justify-between border-b border-token pb-2">
                  <span className="text-subtle-token">Şehir</span>
                  <span className="font-bold text-main-token">{hotel.city}</span>
                </div>
                {hotel.phone ? (
                  <div className="flex justify-between border-b border-token pb-2">
                    <span className="text-subtle-token">Telefon</span>
                    <span className="font-bold text-main-token">{hotel.phone}</span>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        {tours.length > 0 && (
          <section className="mt-14">
            <h2 className="text-2xl font-extrabold text-main-token mb-6">
              Bu Oteli Kullanan Turlar
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {tours.map((tour) => (
                <TourCard key={tour.id} tour={tour} />
              ))}
            </div>
          </section>
        )}
      </main>

      <Footer />
    </div>
  );
}

"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import { useLanguage } from "@/context/LanguageContext";

export interface GalleryTourImage {
  id?: string;
  url: string;
}

export interface GalleryTour {
  id: string;
  title: string;
  description?: string;
  days: number;
  nights: number;
  price: number;
  image_url?: string;
  category?: { name?: string } | null;
  images?: GalleryTourImage[];
}

type TourCardProps = {
  tour: GalleryTour;
  onInspect: (tour: GalleryTour) => void;
};

export function TourCard({ tour, onInspect }: TourCardProps) {
  const { t } = useLanguage();
  const photos = [tour.image_url, ...(tour.images?.map((img) => img.url) ?? [])].filter(
    (url): url is string => Boolean(url),
  );
  const fallback =
    "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80";
  const uniquePhotos = [...new Set(photos)];
  const gallery = uniquePhotos.length > 0 ? uniquePhotos : [fallback];
  const [active, setActive] = useState(0);
  const current = gallery[Math.min(active, gallery.length - 1)] ?? fallback;
  const touchStartX = useRef<number | null>(null);

  const onTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0]?.clientX ?? null;
  };

  const onTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null || gallery.length <= 1) return;
    const deltaX = e.changedTouches[0]?.clientX ?? touchStartX.current;
    const diff = deltaX - touchStartX.current;
    if (Math.abs(diff) < 40) return;
    if (diff < 0) setActive((i) => (i + 1) % gallery.length);
    else setActive((i) => (i - 1 + gallery.length) % gallery.length);
    touchStartX.current = null;
  };

  return (
    <div className="card-token group rounded-2xl overflow-hidden flex flex-col justify-between">
      <div>
        <div
          className="relative h-56 w-full overflow-hidden"
          onTouchStart={onTouchStart}
          onTouchEnd={onTouchEnd}
        >
          <Image
            src={current}
            alt={tour.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent" />

          {gallery.length > 1 && (
            <>
              <button
                type="button"
                aria-label="Önceki fotoğraf"
                onClick={(e) => {
                  e.stopPropagation();
                  setActive((i) => (i - 1 + gallery.length) % gallery.length);
                }}
                className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm hover:bg-black/60 transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <button
                type="button"
                aria-label="Sonraki fotoğraf"
                onClick={(e) => {
                  e.stopPropagation();
                  setActive((i) => (i + 1) % gallery.length);
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm hover:bg-black/60 transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 6l6 6-6 6" />
                </svg>
              </button>
            </>
          )}

          <div className="absolute top-4 left-4 flex flex-col items-start gap-2">
            <span className="px-3 py-1 bg-white/90 backdrop-blur-md text-teal-700 border border-teal-200 rounded-lg text-xs font-extrabold uppercase tracking-wider">
              {tour.days > 1
                ? t("tours.days_nights", { days: tour.days, nights: tour.nights })
                : t("tours.daily")}
            </span>
            {tour.category?.name && (
              <span className="px-3 py-1 bg-brand-token text-white rounded-lg text-xs font-bold uppercase tracking-wider">
                {tour.category.name}
              </span>
            )}
          </div>

          {gallery.length > 1 && (
            <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2">
              {gallery.map((url, i) => (
                <button
                  key={`${i}-${url}`}
                  type="button"
                  aria-label={`Fotoğraf ${i + 1}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActive(i);
                  }}
                  className={`h-1.5 flex-1 rounded-full transition-all ${
                    i === active ? "bg-white" : "bg-white/40 hover:bg-white/70"
                  }`}
                />
              ))}
            </div>
          )}
        </div>

        <div className="p-6 space-y-3">
          <h3 className="text-xl font-bold text-main-token group-hover:text-brand-token transition-colors">
            {tour.title}
          </h3>
          <p className="text-subtle-token text-sm line-clamp-3 leading-relaxed">
            {tour.description}
          </p>
        </div>
      </div>

      <div className="p-6 pt-0 border-t border-slate-100 mt-4 flex items-center justify-between gap-4">
        <div>
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">
            {t("tours.starting_from")}
          </span>
          <span className="text-2xl font-black text-brand-token">
            {tour.price.toLocaleString("tr-TR")} ₺
          </span>
        </div>

        <button
          onClick={() => onInspect(tour)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-50 hover:bg-teal-100 text-teal-700 hover:text-teal-800 border border-teal-200 rounded-xl text-sm font-bold transition-all"
        >
          {t("tours.inspect_details")}
        </button>
      </div>
    </div>
  );
}

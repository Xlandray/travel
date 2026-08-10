"use client";

import { useState } from "react";
import { servicesData } from "@/data/servicesData";
import Link from "next/link";

interface InteractiveCalculatorProps {
  initialSlug?: string;
}

export default function InteractiveCalculator({ initialSlug }: InteractiveCalculatorProps) {
  const [selectedSlug, setSelectedSlug] = useState<string>(
    initialSlug || servicesData[0].slug
  );
  const [widthMeters, setWidthMeters] = useState<number>(2);
  const [heightMeters, setHeightMeters] = useState<number>(1);
  const [quantity, setQuantity] = useState<number>(1);
  const [includeLamination, setIncludeLamination] = useState<boolean>(true);

  const currentService = servicesData.find((s) => s.slug === selectedSlug) || servicesData[0];

  // Price Calculation Logic
  const totalSquareMeters = Number((widthMeters * heightMeters * quantity).toFixed(2));
  const laminationCostPerM2 = includeLamination ? 35 : 0;
  const basePricePerM2 = currentService.unitPriceEstimate + laminationCostPerM2;
  const estimatedTotalPrice = Math.round(totalSquareMeters * basePricePerM2);

  return (
    <div className="card-token p-6 sm:p-8 bg-white-token border-2 border-cyan-token space-y-6 shadow-xs">
      <div className="flex items-center justify-between border-b border-token pb-4 flex-wrap gap-2">
        <div>
          <span className="badge-cyan-token font-bold text-xs uppercase tracking-wider">Otomatik Hesaplama Matriksi</span>
          <h3 className="text-xl font-extrabold text-main-token mt-1">Canlı Baskı Fiyat Hesaplayıcı</h3>
        </div>
        <div className="text-xs font-bold text-brand-token bg-cyan-soft-token px-3 py-1.5 rounded-md border border-cyan-token">
          Anında Fiyat Tahmini
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Controls */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-main-token uppercase tracking-wider mb-1.5">
              1. Baskı / Reklam Hizmet Türü
            </label>
            <select
              value={selectedSlug}
              onChange={(e) => setSelectedSlug(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white-token border border-token rounded-lg text-sm text-main-token font-semibold focus:ring-2 focus:ring-[var(--color-primary)]"
            >
              {servicesData.map((service) => (
                <option key={service.slug} value={service.slug}>
                  {service.codeNumber}. {service.title} ({service.unitPriceEstimate} TL/m²)
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-main-token uppercase tracking-wider mb-1.5">
                En (Metre)
              </label>
              <input
                type="number"
                min="0.5"
                max="50"
                step="0.1"
                value={widthMeters}
                onChange={(e) => setWidthMeters(Math.max(0.1, parseFloat(e.target.value) || 0))}
                className="w-full px-3.5 py-2 bg-white-token border border-token rounded-lg text-sm text-main-token font-mono focus:ring-2 focus:ring-[var(--color-primary)]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-main-token uppercase tracking-wider mb-1.5">
                Boy (Metre)
              </label>
              <input
                type="number"
                min="0.5"
                max="50"
                step="0.1"
                value={heightMeters}
                onChange={(e) => setHeightMeters(Math.max(0.1, parseFloat(e.target.value) || 0))}
                className="w-full px-3.5 py-2 bg-white-token border border-token rounded-lg text-sm text-main-token font-mono focus:ring-2 focus:ring-[var(--color-primary)]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 items-center">
            <div>
              <label className="block text-xs font-bold text-main-token uppercase tracking-wider mb-1.5">
                Adet / Miktar
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full px-3.5 py-2 bg-white-token border border-token rounded-lg text-sm text-main-token font-mono focus:ring-2 focus:ring-[var(--color-primary)]"
              />
            </div>

            <div className="pt-5">
              <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-semibold text-main-token">
                <input
                  type="checkbox"
                  checked={includeLamination}
                  onChange={(e) => setIncludeLamination(e.target.checked)}
                  className="w-4 h-4 rounded text-brand-token focus:ring-brand-token"
                />
                Laminasyon Koruma (+35 TL/m²)
              </label>
            </div>
          </div>
        </div>

        {/* Real-time Calculation Result Box */}
        <div className="bg-white-token p-6 rounded-xl border-2 border-cyan-token flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-subtle-token">Hesaplama Özeti</span>
            <div className="flex justify-between text-sm text-subtle-token border-b border-token pb-2">
              <span>Seçilen Hizmet:</span>
              <span className="font-bold text-main-token">{currentService.title}</span>
            </div>
            <div className="flex justify-between text-sm text-subtle-token border-b border-token pb-2">
              <span>Toplam Alan:</span>
              <span className="font-bold text-main-token font-mono">{totalSquareMeters} m²</span>
            </div>
            <div className="flex justify-between text-sm text-subtle-token border-b border-token pb-2">
              <span>Birim Fiyat:</span>
              <span className="font-bold text-main-token font-mono">{basePricePerM2} TL / m²</span>
            </div>
          </div>

          <div className="pt-2">
            <div className="text-xs text-subtle-token font-bold">Tahmini Toplam Tutar (KDV Hariç)</div>
            <div className="text-3xl font-extrabold text-brand-token font-mono tracking-tight mt-1">
              ₺{estimatedTotalPrice.toLocaleString("tr-TR")} <span className="text-xs text-subtle-token font-normal">TL</span>
            </div>
          </div>

          <Link
            href={`/iletisim?service=${selectedSlug}&w=${widthMeters}&h=${heightMeters}&q=${quantity}&price=${estimatedTotalPrice}`}
            className="btn-primary-token w-full justify-center py-3 text-sm font-bold shadow-xs"
          >
            Bu Teklifi Resmi Talebe Dönüştür →
          </Link>
        </div>
      </div>
    </div>
  );
}

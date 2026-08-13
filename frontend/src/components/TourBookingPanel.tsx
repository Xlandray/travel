"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";

export interface BookingDeparture {
  id: string;
  start_date: string;
  end_date: string;
  price: number;
  available_seats: number;
}

export interface BookingBoardingPoint {
  id: string;
  name: string;
}

type TourBookingPanelProps = {
  departures: BookingDeparture[];
  boardingPoints: BookingBoardingPoint[];
};

export function TourBookingPanel({ departures, boardingPoints }: TourBookingPanelProps) {
  const { t } = useLanguage();
  const router = useRouter();
  const [departureId, setDepartureId] = useState(departures[0]?.id ?? "");
  const [boardingPointId, setBoardingPointId] = useState(boardingPoints[0]?.id ?? "");

  const activeDeparture = departures.find((d) => d.id === departureId) ?? departures[0];

  const handleProceed = () => {
    const params = new URLSearchParams();
    if (departureId) params.append("departure", departureId);
    if (boardingPointId) params.append("boarding_point", boardingPointId);
    router.push(`/checkout?${params.toString()}`);
  };

  return (
    <div className="card-token bg-surface-token rounded-2xl p-6 space-y-4 shadow-lg">
      <h4 className="text-lg font-extrabold text-main-token">{t("booking.modal_subtitle")}</h4>

      {departures.length === 0 ? (
        <div className="p-4 bg-canvas-token border border-token rounded-xl text-subtle-token text-sm">
          {t("booking.no_departures")}
        </div>
      ) : (
        <>
          <div>
            <label
              htmlFor="booking-departure"
              className="block text-xs font-bold text-subtle-token uppercase mb-2"
            >
              {t("booking.departure_date")}
            </label>
            <select
              id="booking-departure"
              value={departureId}
              onChange={(e) => setDepartureId(e.target.value)}
              className="input-token"
            >
              {departures.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.start_date} → {d.end_date} · {Number(d.price).toLocaleString("tr-TR")} ₺ ·{" "}
                  {d.available_seats} {t("booking.seats")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="booking-boarding-point"
              className="block text-xs font-bold text-subtle-token uppercase mb-2"
            >
              {t("booking.boarding_point")}
            </label>
            <select
              id="booking-boarding-point"
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

          {activeDeparture && (
            <div className="flex items-center justify-between text-sm py-2 border-t border-token">
              <span className="text-subtle-token">{t("booking.unit_price")}</span>
              <span className="text-xl font-bold text-brand-token">
                {Number(activeDeparture.price).toLocaleString("tr-TR")} ₺
              </span>
            </div>
          )}

          <button
            onClick={handleProceed}
            className="btn-primary-token w-full py-3 rounded-xl shadow-lg transition-all"
          >
            {t("booking.submit_button")}
          </button>
        </>
      )}
    </div>
  );
}

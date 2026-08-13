/**
 * The shapes the API actually returns.
 *
 * These were previously re-declared in every page that fetched them, with
 * small differences: one file had `boarding_points: BoardingPoint[]`, another
 * `{ id: string; name: string }[]`. Both compiled, so nothing said which one
 * matched the backend.
 */

export interface BoardingPoint {
  id: string;
  name: string;
  description?: string;
}

export interface TourCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active?: boolean;
}

export interface TourImage {
  id: string;
  url: string;
  sort_order: number;
}

export interface Hotel {
  id: string;
  name: string;
  slug?: string;
  city: string;
  star_rating?: number;
  description?: string | null;
  image_url?: string | null;
}

export interface TourHotel {
  id: string;
  night_order: number;
  hotel: Hotel;
}

export interface RouteStop {
  id: string;
  day_number: number;
  title: string;
  description?: string;
  boarding_points: BoardingPoint[];
}

export interface TourDeparture {
  id: string;
  start_date: string;
  end_date: string;
  price: number;
  available_seats: number;
  total_quota?: number;
}

export interface Tour {
  id: string;
  title: string;
  slug: string;
  description: string;
  days: number;
  nights: number;
  price: number;
  image_url?: string;
  category?: TourCategory | null;
  images?: TourImage[];
  hotels?: TourHotel[];
  route_stops?: RouteStop[];
  departures: TourDeparture[];
  boarding_points: BoardingPoint[];
}

export type BookingStatus = "pending" | "confirmed" | "cancelled";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";
export type PaymentMethod = "card" | "transfer";

export interface Booking {
  id: string;
  departure_id: string;
  boarding_point_id: string | null;
  seat_count: number;
  total_price: number;
  status: BookingStatus;
  created_at: string;
  tour_title?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  boarding_point_name?: string | null;
  payment_id?: string | null;
  payment_status?: PaymentStatus | null;
}

export interface Payment {
  id: string;
  booking_id: string;
  amount: number;
  method: PaymentMethod;
  status: PaymentStatus;
  transaction_id?: string | null;
  paid_at?: string | null;
  refunded_at?: string | null;
}

export interface Content {
  id: string;
  title: string;
  slug: string;
  body: string;
  is_published: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

/** `GET /public/settings` — a flat key/value map of site settings. */
export type PublicSettings = Record<string, string>;

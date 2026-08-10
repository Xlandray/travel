import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ContactForm from "./ContactForm";
import Breadcrumbs from "@/components/Breadcrumbs";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "İletişim & Fabrika Adresi",
  description: "Armonitex & UPD Açıkhava Çözümleri iletişim bilgileri, Ümraniye Dudullu üretim tesisi adresi ve teklif formu.",
  alternates: {
    canonical: "/iletisim",
  },
  openGraph: {
    title: "İletişim | Armonitex Dijital Baskı & Açıkhava Çözümleri",
    description: "Yukarı Dudullu, Edep Sk. No:9, 34775 Ümraniye/İstanbul tesisimizden hızlı teklif ve bilgi alın.",
    url: "https://armonitex.com.tr/iletisim",
  },
};

export default function IletisimPage() {
  return (
    <div className="min-h-screen bg-white-token flex flex-col font-sans text-main-token">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        <Breadcrumbs items={[{ label: "İletişim" }]} />

        {/* Page Title Header */}
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <span className="badge-cyan-token font-bold text-xs">Ümraniye Üretim Tesisi</span>
          <h1 className="text-4xl font-extrabold text-main-token tracking-tight">Bizimle İletişime Geçin</h1>
          <p className="text-subtle-token text-base">
            Projenizin detaylarını iletin veya Ümraniye tesisimizi ziyaret ederek baskı numunelerimizi yerinde inceleyin.
          </p>
        </div>

        {/* Main Grid: Contact Info & Form */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Contact Cards */}
          <div className="lg:col-span-5 space-y-6">
            <div className="card-token p-6 bg-white-token border-2 border-cyan-token space-y-4">
              <h2 className="text-xl font-bold text-main-token border-b border-token pb-3">İletişim Bilgileri</h2>
              
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-xs font-bold text-subtle-token uppercase tracking-wider">Fabrika &amp; Üretim Adresi</div>
                  <div className="font-semibold text-main-token mt-1">
                    Armoni Reklam &amp; UPD Açıkhava Çözümleri
                  </div>
                  <div className="text-subtle-token mt-0.5 leading-relaxed">
                    Yukarı Dudullu, Edep Sk. No:9<br />
                    34775 Ümraniye / İstanbul, Türkiye
                  </div>
                </div>

                <div className="pt-2 border-t border-token">
                  <div className="text-xs font-bold text-subtle-token uppercase tracking-wider">E-posta</div>
                  <a href="mailto:info@armonitex.com.tr" className="text-brand-token font-semibold hover:underline mt-0.5 block">
                    info@armonitex.com.tr
                  </a>
                </div>

                <div className="pt-2 border-t border-token">
                  <div className="text-xs font-bold text-subtle-token uppercase tracking-wider">Telefon</div>
                  <a href="tel:+902160000000" className="text-brand-token font-bold text-base hover:underline mt-0.5 block">
                    0 (216) 000 00 00
                  </a>
                </div>

                <div className="pt-2 border-t border-token">
                  <div className="text-xs font-bold text-subtle-token uppercase tracking-wider">Çalışma Saatleri</div>
                  <div className="text-subtle-token mt-0.5">
                    Hafta İçi: 08:30 - 18:30<br />
                    Cumartesi: 09:00 - 14:00
                  </div>
                </div>
              </div>

              <div className="pt-4">
                <a
                  href="https://maps.google.com/?q=Yukarı+Dudullu+Edep+Sk+No+9+34775+Ümraniye+İstanbul"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary-token text-xs py-2 w-full justify-center"
                >
                  📍 Google Haritalar&apos;da Yol Tarifi Al ↗
                </a>
              </div>
            </div>
          </div>

          {/* Right Column: Contact & Quotation Form */}
          <div className="lg:col-span-7">
            <ContactForm />
          </div>
        </div>

        {/* Dynamic Interactive Google Map Location */}
        <section className="space-y-4 pt-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <h2 className="text-2xl font-bold text-main-token">Üretim Tesisimiz Konumu</h2>
            <span className="text-xs font-bold text-subtle-token bg-cyan-soft-token px-3 py-1 rounded-full border border-cyan-token">
              📍 Yukarı Dudullu, Edep Sk. No:9, 34775 Ümraniye/İstanbul
            </span>
          </div>

          <div className="rounded-2xl overflow-hidden border-2 border-cyan-token shadow-md h-[400px] relative bg-canvas-token">
            <iframe
              title="Armonitex Ümraniye Tesis Konumu"
              src="https://maps.google.com/maps?q=Yukarı%20Dudullu%2C%20Edep%20Sk.%20No%3A9%2C%2034775%20%C3%9Cmraniye%2F%C4%B0stanbul&t=&z=16&ie=UTF8&iwloc=&output=embed"
              width="100%"
              height="100%"
              style={{ border: 0 }}
              allowFullScreen={false}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
            />
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

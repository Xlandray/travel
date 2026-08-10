"use client";
import { useState } from "react";

export default function ArchitectureTabs() {
  const [activeTab, setActiveTab] = useState<"indoor_outdoor" | "signage" | "display" | "tech">("indoor_outdoor");

  const tabContents = {
    indoor_outdoor: {
      title: "İç Mekan & Dış Mekan Dijital Baskı",
      description: "1998'den beri en yüksek çözünürlüklü dijital baskı teknolojileri ile poster, afiş, vinil baskı, mesh baskı, kanvas ve araç giydirme çözümleri sunuyoruz.",
      features: [
        "Yüksek Çözünürlüklü Eco-Solvent Baskı",
        "Dayanıklı Dış Mekan Vinil & Mesh Baskı",
        "Araç ve Bina Cephe Giydirme Üretimi",
        "UV Korumalı Solmaz Renk Kalitesi"
      ],
      badge: "İç & Dış Mekan Baskı",
    },
    signage: {
      title: "Açıkhava Tabelaları & Yönlendirme Levhaları",
      description: "Markanızın görünürlüğünü en üst seviyeye çıkaran ışıklı/ışıksız tabela sistemleri, totem tabelalar ve kurumsal yönlendirme levhaları imalatı.",
      features: [
        "Işıklı & Işıksız Tabela İmalatı",
        "Pleksi & Alüminyum Kutu Harf Sistemleri",
        "Kurumsal İç Mekan Yönlendirmeleri",
        "Bina Çatı & Cephe Totem Üretimi"
      ],
      badge: "Açıkhava & Tabela",
    },
    display: {
      title: "Display & Fuar Tanıtım Ekipmanları",
      description: "Fuar, lansman ve etkinlikleriniz için taşınabilir, kurulumu kolay ve yüksek kaliteli tanıtım malzemeleri üretimi.",
      features: [
        "Alüminyum Kasalı Roll-up Standlar",
        "Modüler Örümcek Stand & Örümcek Masalar",
        "Plaj Bayrak, Flama & Kırlangıç Flama",
        "Foreks, Dekota & Fotoblok Baskı Çözümleri"
      ],
      badge: "Display & Fuar",
    },
    tech: {
      title: "1998'den Beri İleri Üretim Teknolojimiz",
      description: "Tüm baskı ve montaj aşamalarını kendi bünyemizde gerçekleştirebilecek makine parkuru ve uzman teknik ekibimizle 7/24 hizmetinizdeyiz.",
      features: [
        "Japon Teknoloji Dijital Baskı Makineleri",
        "Renk Kalibrasyonel Spektrofotometre Takibi",
        "Bünyemizde Tam Otomatik Kesim & Sonlama",
        "Profesyonel Saha Montaj ve Uygulama Ekibi"
      ],
      badge: "Üretim Altyapısı",
    },
  };

  const current = tabContents[activeTab];

  return (
    <div className="w-full bg-white-token rounded-xl border border-token p-6 sm:p-10 shadow-xs">
      {/* Tab Navigation Buttons */}
      <div className="flex flex-wrap gap-2 mb-8 border-b border-token pb-4">
        <button
          onClick={() => setActiveTab("indoor_outdoor")}
          className={`px-4 py-2.5 rounded-md font-bold text-sm transition-all duration-150 flex items-center gap-2 ${
            activeTab === "indoor_outdoor"
              ? "bg-[var(--color-primary)] text-white-token shadow-sm"
              : "bg-white-token text-subtle-token border border-token hover:border-[var(--color-primary)] hover:text-brand-token"
          }`}
        >
          <span>🖨️</span> Dijital Baskı
        </button>
        <button
          onClick={() => setActiveTab("signage")}
          className={`px-4 py-2.5 rounded-md font-bold text-sm transition-all duration-150 flex items-center gap-2 ${
            activeTab === "signage"
              ? "bg-[var(--color-primary)] text-white-token shadow-sm"
              : "bg-white-token text-subtle-token border border-token hover:border-[var(--color-primary)] hover:text-brand-token"
          }`}
        >
          <span>🏢</span> Tabelalar & Yönlendirme
        </button>
        <button
          onClick={() => setActiveTab("display")}
          className={`px-4 py-2.5 rounded-md font-bold text-sm transition-all duration-150 flex items-center gap-2 ${
            activeTab === "display"
              ? "bg-[var(--color-primary)] text-white-token shadow-sm"
              : "bg-white-token text-subtle-token border border-token hover:border-[var(--color-primary)] hover:text-brand-token"
          }`}
        >
          <span>🎯</span> Display & Fuar
        </button>
        <button
          onClick={() => setActiveTab("tech")}
          className={`px-4 py-2.5 rounded-md font-bold text-sm transition-all duration-150 flex items-center gap-2 ${
            activeTab === "tech"
              ? "bg-[var(--color-primary)] text-white-token shadow-sm"
              : "bg-white-token text-subtle-token border border-token hover:border-[var(--color-primary)] hover:text-brand-token"
          }`}
        >
          <span>⚙️</span> Üretim Teknolojisi
        </button>
      </div>

      {/* Content Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center bg-white-token">
        <div className="space-y-4">
          <div className="inline-block badge-cyan-token font-bold">
            {current.badge}
          </div>
          <h3 className="text-2xl font-extrabold text-main-token tracking-tight">{current.title}</h3>
          <p className="text-subtle-token text-base leading-relaxed">{current.description}</p>
        </div>

        {/* Feature List Container - Pure White & Crisp Cyan Border */}
        <div className="bg-white-token border-2 border-cyan-token rounded-xl p-6 space-y-3 shadow-xs">
          <h4 className="text-xs font-bold uppercase tracking-wider text-brand-token mb-2">
            Öne Çıkan Standartlarımız
          </h4>
          <ul className="space-y-3">
            {current.features.map((item, idx) => (
              <li key={idx} className="flex items-center gap-3 text-sm font-semibold text-main-token">
                <span className="w-5 h-5 rounded-full bg-[var(--color-primary)] text-white-token flex items-center justify-center text-xs font-bold shrink-0">
                  ✓
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

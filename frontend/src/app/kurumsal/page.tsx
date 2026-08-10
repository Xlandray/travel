import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ArchitectureTabs from "@/components/ArchitectureTabs";
import Breadcrumbs from "@/components/Breadcrumbs";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hakkımızda & Kurumsal",
  description: "1998'den bu yana 28 yıllık tecrübesiyle Armoni Reklam & UPD Reklam bünyesinde dijital baskı ve açıkhava reklam üretimi.",
  alternates: {
    canonical: "/kurumsal",
  },
  openGraph: {
    title: "Kurumsal | Armonitex Dijital Baskı & Açıkhava Çözümleri",
    description: "28 yıllık sektör liderliği, yüksek kapasiteli baskı parkuru ve müşteri odaklı çözümlerimiz.",
    url: "https://armonitex.com.tr/kurumsal",
  },
};

export default function KurumsalPage() {
  return (
    <div className="min-h-screen bg-white-token flex flex-col font-sans text-main-token">
      <Header />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        <Breadcrumbs items={[{ label: "Kurumsal" }]} />

        {/* Corporate Header Banner */}
        <section className="bg-navy-token text-white-token p-8 md:p-12 rounded-2xl shadow-md space-y-4">
          <span className="badge-cyan-token font-bold text-xs">Armoni Reklam &amp; UPD Açıkhava Çözümleri</span>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            28 Yıllık Sektör Otoritesi ve İmalat Gücü
          </h1>
          <p className="text-cyan-100 text-base md:text-lg max-w-3xl leading-relaxed">
            1998 yılında kurulan Armoni Reklam ve grup markamız UPD Açıkhava Çözümleri ile Türkiye&apos;nin önde gelen kurumsal markalarına iç mekan, dış mekan dijital baskı ve reklam çözümleri sunuyoruz.
          </p>
        </section>

        {/* Story & Vision */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="card-token p-6 sm:p-8 bg-white-token space-y-4">
            <h2 className="text-xl font-bold text-main-token border-b border-token pb-2">Tarihçemiz &amp; Kuruluş</h2>
            <p className="text-subtle-token text-sm leading-relaxed">
              1998 yılında İstanbul&apos;da temelleri atılan firmamız, dijital baskı teknolojilerinin gelişimiyle birlikte parkurunu sürekli yenilemiş ve bugün Ümraniye Şerifali tesislerinde yüksek kapasiteli üretim gerçekleştiren bir entegre tesis haline gelmiştir.
            </p>
            <p className="text-subtle-token text-sm leading-relaxed">
              UPD Açıkhava Çözümleri markamızla büyük ölçekli bina cephe giydirme, totem tabela imalatı ve mağaza konsept uygulamalarında uzmanlaşmış bulunuyoruz.
            </p>
          </div>

          <div className="card-token p-6 sm:p-8 bg-white-token space-y-4">
            <h2 className="text-xl font-bold text-main-token border-b border-token pb-2">Kalite &amp; Sürdürülebilirlik</h2>
            <p className="text-subtle-token text-sm leading-relaxed">
              Üretim süreçlerimizde insan sağlığına zararsız, kokusuz eko-solvent ve UV mürekkepler tercih edilmektedir. Tüm atık folyo ve alüminyum malzemelerimiz geri dönüşüm protokollerine uygun şekilde işlenir.
            </p>
            <ul className="space-y-2 text-xs font-semibold text-main-token">
              <li className="flex items-center gap-2">
                <span className="text-brand-token font-bold">✓</span> %100 Orijinal Malzeme Garantisi
              </li>
              <li className="flex items-center gap-2">
                <span className="text-brand-token font-bold">✓</span> 7/24 Kesintisiz Vardiyalı İmalat
              </li>
              <li className="flex items-center gap-2">
                <span className="text-brand-token font-bold">✓</span> Profesyonel Sahada Montaj Ekibi
              </li>
            </ul>
          </div>
        </section>

        {/* Interactive Production Tabs Component */}
        <section className="pt-6">
          <h2 className="text-2xl font-bold text-main-token mb-6 text-center">Tesis Altyapımız ve Üretim Standartlarımız</h2>
          <ArchitectureTabs />
        </section>
      </main>

      <Footer />
    </div>
  );
}

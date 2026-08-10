import Header from "@/components/Header";
import Footer from "@/components/Footer";
import InteractiveCalculator from "@/components/InteractiveCalculator";
import { servicesData } from "@/data/servicesData";
import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";

export async function generateStaticParams() {
  return servicesData.map((service) => ({
    slug: service.slug,
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const resolvedParams = await params;
  const service = servicesData.find((s) => s.slug === resolvedParams.slug);

  if (!service) {
    return { title: "Hizmet Bulunamadı" };
  }

  return {
    title: `${service.title} İmalatı & Fiyatları`,
    description: `${service.shortDesc} Armonitex 28 yıllık tecrübesiyle Şerifali Ümraniye tesisinde hızlı imalat ve montaj imkanı.`,
    keywords: service.seoKeywords,
    alternates: {
      canonical: `/hizmet/${service.slug}`,
    },
    openGraph: {
      title: `${service.title} İmalatı & Fiyatları | Armonitex`,
      description: service.shortDesc,
      url: `https://armonitex.com.tr/hizmet/${service.slug}`,
      type: "website",
    },
  };
}

export default async function ServiceDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const resolvedParams = await params;
  const service = servicesData.find((s) => s.slug === resolvedParams.slug);

  if (!service) notFound();

  // Service Schema.org Structured Data
  const serviceJsonLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: service.title,
    serviceType: service.title,
    provider: {
      "@type": "LocalBusiness",
      name: "Armonitex Dijital Baskı & Açıkhava Çözümleri",
      address: {
        "@type": "PostalAddress",
        streetAddress: "Yukarı Dudullu, Edep Sk. No:9, 34775",
        addressLocality: "Ümraniye",
        addressRegion: "İstanbul",
        addressCountry: "TR"
      }
    },
    description: service.fullDescription,
    offers: {
      "@type": "Offer",
      price: service.unitPriceEstimate,
      priceCurrency: "TRY",
      availability: "https://schema.org/InStock"
    }
  };

  // SSS Schema
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: service.faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer
      }
    }))
  };

  return (
    <div className="min-h-screen bg-white-token flex flex-col font-sans text-main-token">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(serviceJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />

      <Header />

      {/* Hero Section */}
      <section className="bg-white-token border-b border-token py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-4">
          <div className="flex items-center gap-3">
            <span className="badge-cyan-token font-bold text-xs font-mono">{service.codeNumber}</span>
            <span className="badge-cyan-token font-bold text-xs">{service.badge}</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-main-token">
            {service.title} İmalat &amp; Uygulama
          </h1>
          <p className="text-subtle-token text-lg max-w-3xl leading-relaxed">
            {service.shortDesc}
          </p>
        </div>
      </section>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
        {/* Full Description Card */}
        <div className="card-token p-8 md:p-10 space-y-6 bg-white-token">
          <h2 className="text-2xl font-bold text-main-token border-b border-token pb-3">
            Üretim &amp; Teknik Özellikler
          </h2>
          <p className="text-subtle-token leading-relaxed text-base">
            {service.fullDescription}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            <div className="space-y-3">
              <h3 className="font-bold text-main-token text-base">Öne Çıkan Özellikler</h3>
              <ul className="space-y-2 text-sm text-subtle-token">
                {service.features.map((feat, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-brand-token font-bold">✓</span>
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-3">
              <h3 className="font-bold text-main-token text-base">Teknik Detaylar</h3>
              <div className="space-y-2 text-sm">
                {service.specifications.map((spec, idx) => (
                  <div key={idx} className="flex justify-between border-b border-token pb-1.5 text-subtle-token">
                    <span className="font-semibold text-main-token">{spec.label}:</span>
                    <span className="font-mono">{spec.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Live Instant Calculator */}
        <InteractiveCalculator initialSlug={service.slug} />

        {/* FAQs */}
        {service.faqs.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-main-token">Sıkça Sorulan Sorular</h2>
            <div className="space-y-4">
              {service.faqs.map((faq, idx) => (
                <div key={idx} className="card-token p-6 bg-white-token border-2 border-cyan-token space-y-2">
                  <h3 className="text-base font-bold text-main-token">{faq.question}</h3>
                  <p className="text-sm text-subtle-token leading-relaxed">{faq.answer}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Other Services Navigation */}
        <div className="pt-8 border-t border-token space-y-6">
          <h2 className="text-xl font-bold text-main-token">Diğer Baskı &amp; Reklam Hizmetlerimiz</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {servicesData
              .filter((s) => s.slug !== service.slug)
              .map((other) => (
                <Link
                  key={other.slug}
                  href={`/hizmet/${other.slug}`}
                  className="card-token p-4 bg-white-token hover:border-cyan-token transition-colors flex flex-col justify-between"
                >
                  <div className="text-xs font-bold text-subtle-token font-mono mb-1">{other.codeNumber}</div>
                  <h3 className="font-bold text-sm text-main-token">{other.title}</h3>
                  <span className="text-xs font-semibold text-brand-token mt-2">Detayları İncele →</span>
                </Link>
              ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

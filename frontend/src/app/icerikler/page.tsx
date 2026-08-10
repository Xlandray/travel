import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Haberler & Projeler",
  description: "Armonitex tarafından tamamlanan dijital baskı projeleri, hammadde teknolojileri ve sektör haberleri.",
  alternates: {
    canonical: "/icerikler",
  },
  openGraph: {
    title: "Haberler & Projeler | Armonitex Dijital Baskı",
    description: "Tamamlanan açıkhava reklam projelerimiz ve sektör duyurularımız.",
    url: "https://armonitex.com.tr/icerikler",
  },
};

interface Content {
  id: string;
  title: string;
  slug: string;
  body: string;
  is_published: boolean;
  created_at?: string;
}

async function getPublishedContents(): Promise<Content[]> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/contents`, {
      next: { revalidate: 60 },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) return [];
    const contents: Content[] = await res.json();
    return contents.filter((c) => c.is_published);
  } catch {
    return [];
  }
}

export default async function ContentsListingPage() {
  const contents = await getPublishedContents();

  return (
    <div className="min-h-screen bg-white-token flex flex-col font-sans text-main-token">
      <Header />

      <section className="bg-navy-token text-white-token py-16 px-4 sm:px-6 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto space-y-4">
          <h1 className="text-4xl font-extrabold tracking-tight">Haberler &amp; Tamamlanan Projeler</h1>
          <p className="text-cyan-100/90 text-base max-w-xl mx-auto">
            1998&apos;den bu yana imza attığımız büyük ölçekli açıkhava baskı projeleri ve sektör gelişmeleri.
          </p>
        </div>
      </section>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {contents.length === 0 ? (
          <div className="bg-white-token p-12 rounded-2xl border-2 border-cyan-token text-center space-y-3">
            <div className="text-4xl">📚</div>
            <h2 className="text-lg font-semibold text-main-token">Henüz yayınlanmış bir haber bulunmuyor.</h2>
            <p className="text-sm text-subtle-token">Çok yakında yeni proje duyurularımız eklenecektir.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {contents.map((content) => (
              <article
                key={content.id}
                className="card-token p-6 flex flex-col justify-between bg-white-token"
              >
                <div>
                  <div className="inline-block px-3 py-1 badge-cyan-token font-semibold text-xs rounded-full mb-4">
                    Sektörel Yayın
                  </div>
                  <h2 className="text-xl font-bold text-main-token mb-3">{content.title}</h2>
                  <p className="text-subtle-token text-sm line-clamp-4 mb-6 leading-relaxed">
                    {content.body}
                  </p>
                </div>

                <Link
                  href={`/icerik/${content.slug}`}
                  className="inline-flex items-center text-sm font-semibold text-brand-token hover:underline pt-4 border-t border-token"
                >
                  Devamını Oku →
                </Link>
              </article>
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

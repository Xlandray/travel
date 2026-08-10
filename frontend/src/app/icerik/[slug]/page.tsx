import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

interface Content {
  id: string;
  title: string;
  slug: string;
  body: string;
  is_published: boolean;
  created_at?: string;
  updated_at?: string;
}

async function getContentBySlug(slug: string): Promise<Content | null> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/contents`, {
      next: { revalidate: 60 },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) return null;
    const contents: Content[] = await res.json();
    return contents.find((c) => c.slug === slug && c.is_published) || null;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const resolvedParams = await params;
  const content = await getContentBySlug(resolvedParams.slug);

  if (!content) {
    return {
      title: "İçerik Bulunamadı",
    };
  }

  return {
    title: content.title,
    description: content.body.slice(0, 160),
    alternates: {
      canonical: `/icerik/${content.slug}`,
    },
    openGraph: {
      title: content.title,
      description: content.body.slice(0, 160),
      url: `https://armonitex.com.tr/icerik/${content.slug}`,
      type: "article",
    },
  };
}

export default async function ContentDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const resolvedParams = await params;
  const content = await getContentBySlug(resolvedParams.slug);
  if (!content) notFound();

  // JSON-LD Schema nesnesi (Structured Data for Search Engines)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: content.title,
    datePublished: content.created_at || new Date().toISOString(),
    url: `https://armonitex.com.tr/icerik/${content.slug}`,
    author: {
      "@type": "Organization",
      name: "Armonitex",
    },
  };

  return (
    <div className="min-h-screen bg-white-token flex flex-col font-sans text-main-token">
      {/* JSON-LD verisini sayfanın head kısmına sessizce gömüyoruz */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      
      <Header />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <article className="card-token p-8 md:p-12 bg-white-token">
          <Link
            href="/"
            className="inline-flex items-center text-sm font-semibold text-brand-token hover:underline mb-6"
          >
            ← Ana Sayfaya Dön
          </Link>

          <h1 className="text-3xl md:text-4xl font-extrabold text-main-token mb-6 leading-tight">
            {content.title}
          </h1>

          <div className="prose max-w-none text-subtle-token leading-relaxed space-y-4">
            {content.body.split("\n").map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </div>
        </article>
      </main>

      <Footer />
    </div>
  );
}

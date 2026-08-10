import Link from "next/link";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  // Generate Schema.org BreadcrumbList JSON-LD
  const breadcrumbListJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "Ana Sayfa",
        item: "https://armonitex.com.tr",
      },
      ...items.map((item, index) => ({
        "@type": "ListItem",
        position: index + 2,
        name: item.label,
        item: item.href ? `https://armonitex.com.tr${item.href}` : undefined,
      })),
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbListJsonLd) }}
      />
      <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-xs font-semibold text-subtle-token">
        <Link href="/" className="hover:text-brand-token transition-colors flex items-center gap-1">
          Ana Sayfa
        </Link>
        {items.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span className="text-subtle-token/40">/</span>
            {item.href ? (
              <Link href={item.href} className="hover:text-brand-token transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className="text-main-token font-bold">{item.label}</span>
            )}
          </div>
        ))}
      </nav>
    </>
  );
}

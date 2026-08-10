import { MetadataRoute } from "next";
import { servicesData } from "@/data/servicesData";

interface ContentItem {
  slug: string;
  is_published: boolean;
  created_at?: string;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // 1. Sabit Sayfalar (Statik Rotalar)
  const staticRoutes = ["", "/kurumsal", "/icerikler", "/iletisim", "/auth/login", "/auth/register"].map((route) => ({
    url: `https://armonitex.com.tr${route}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: route === "" ? 1 : 0.8,
  }));

  // 2. Programmatik SEO Hizmet Landing Sayfaları (/hizmet/[slug])
  const serviceRoutes = servicesData.map((service) => ({
    url: `https://armonitex.com.tr/hizmet/${service.slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.9,
  }));

  // 3. FastAPI'den Dinamik İçerikleri Çekme (Timeout korumalı)
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/contents`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) return [...staticRoutes, ...serviceRoutes];
    
    const contents: ContentItem[] = await res.json();
    const dynamicRoutes = contents
      .filter((content) => content.is_published)
      .map((content) => ({
        url: `https://armonitex.com.tr/icerik/${content.slug}`,
        lastModified: new Date(content.created_at || Date.now()), 
        changeFrequency: "monthly" as const,
        priority: 0.7,
      }));

    return [...staticRoutes, ...serviceRoutes, ...dynamicRoutes];
  } catch {
    return [...staticRoutes, ...serviceRoutes];
  }
}

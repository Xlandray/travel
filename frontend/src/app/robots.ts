import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/auth/forgot-password"], // Botların girmesini istemediğimiz yerler
    },
    sitemap: "https://armonitex.com.tr/sitemap.xml", // Dinamik sitemap adresimiz
  };
}

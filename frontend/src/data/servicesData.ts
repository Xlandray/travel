export interface ServiceItem {
  id: string;
  slug: string;
  title: string;
  shortDesc: string;
  badge: string;
  codeNumber: string;
  unitPriceEstimate: number; // TL / m2 base for calculator
  fullDescription: string;
  features: string[];
  specifications: { label: string; value: string }[];
  faqs: { question: string; answer: string }[];
  seoKeywords: string[];
}

export const servicesData: ServiceItem[] = [
  {
    id: "01",
    slug: "ic-mekan-dijital-baski",
    title: "İç Mekan Dijital Baskı",
    shortDesc: "Yüksek çözünürlüklü poster, afiş, kanvas tablo, duratrans ve fotoblok iç mekan grafik baskıları.",
    badge: "1440 DPI High-Res",
    codeNumber: "01",
    unitPriceEstimate: 250,
    fullDescription: "Armonitex iç mekan dijital baskı tesislerimizde, kokusuz ve çevre dostu su bazlı ve pigment mürekkepler ile mağaza içi görseller, sergi panoları, kanvas tablolar ve yüksek kaliteli poster üretimi gerçekleştirmekteyiz. 1440 DPI yüksek çözünürlüklü baskı teknolojimiz ile en ince detayları ve canlı renkleri kusursuz biçimde yansıtıyoruz.",
    features: [
      "1440 DPI İleri Çözünürlüklü Baskı Kalitesi",
      "Kokusuz ve İnsan Sağlığına Zararsız Eko-Solvent & Pigment Mürekkep",
      "Fotoblok, Foreks (PVC Dekota) ve Paspartu Sıvama Opsiyonları",
      "Mat, Parlak ve Dokulu Laminasyon Koruma Seçenekleri"
    ],
    specifications: [
      { label: "Maksimum En", value: "160 cm (Kesintisiz Tek Parça)" },
      { label: "Baskı Çözünürlüğü", value: "1440 DPI High-Res" },
      { label: "Malzeme Çeşitleri", value: "Kuşe Kağıt, PP Film, Duratrans, Kanvas, Fotoblok" },
      { label: "Teslimat Süresi", value: "24-48 Saat" }
    ],
    faqs: [
      {
        question: "İç mekan baskılarında renk solması yaşanır mı?",
        answer: "Kullandığımız UV korumalı laminasyon ve kaliteli pigment mürekkepler sayesinde iç mekan baskılarımız solmaya karşı 5 yıldan fazla dayanıklılık garantisine sahiptir."
      },
      {
        question: "İç mekan baskıları su ve nemden etkilenir mi?",
        answer: "Laminasyon kaplamalı ürünlerimiz nem ve silinebilir yüzey korumasına sahiptir."
      }
    ],
    seoKeywords: [
      "İç Mekan Dijital Baskı",
      "Poster Baskı İstanbul",
      "Kanvas Tablo İmalatı",
      "Duratrans Baskı",
      "Fotoblok Sıvama",
      "Ümraniye Dijital Baskı"
    ]
  },
  {
    id: "02",
    slug: "dis-mekan-vinil-baski",
    title: "Dış Mekan Vinil & Mesh Baskı",
    shortDesc: "Zorlu hava şartlarına dayanıklı vinil (branda), delikli mesh ve bina cephe giydirme baskıları.",
    badge: "Ağır Gramaj Dökme Vinil",
    codeNumber: "02",
    unitPriceEstimate: 180,
    fullDescription: "Dış mekan tanıtım projeleriniz için fırtına, yağmur ve yoğun güneş ışığına dayanıklı ağır gramajlı dökme vinil ve rüzgar geçiren delikli mesh baskı üretimi sağlamaktayız. Şerifali tesisimizde ürettiğimiz vinil baskılar kolon dikişli, kapsüllü ve montaja hazır halde teslim edilir.",
    features: [
      "440g - 510g Avrupa Dökme Vinil (Branda) Kullanımı",
      "Rüzgar Dirençli Delikli Mesh (File) Baskı Teknolojisi",
      "UV Dayanımlı Solmaz Dış Mekan Mürekkepleri",
      "Kolon Takviyeli Kenar Dikişi ve Pirinç Kapsül Halka İşlemçiliği"
    ],
    specifications: [
      { label: "Maksimum Rulo Eni", value: "320 cm ve 500 cm (Kaynaklı Sınırsız)" },
      { label: "Gramaj Ağırlığı", value: "280g - 510g / m²" },
      { label: "Dış Mekan Ömrü", value: "3 - 5 Yıl Güneş & Rüzgar Dayanımı" },
      { label: "Montaj Desteği", value: "İstanbul Geneli Vinçli Cephe Montajı" }
    ],
    faqs: [
      {
        question: "Delikli Mesh baskı rüzgarlı binalarda yırtılır mı?",
        answer: "Mesh baskılar üzerindeki mikro delikler sayesinde rüzgarı geçirir ve yelken etkisi oluşturmaz. Kenar kolon takviyeleri ile ekstra sağlamlaştırılır."
      }
    ],
    seoKeywords: [
      "Dış Mekan Vinil Baskı",
      "Branda Baskı Fiyatları",
      "Mesh Baskı İstanbul",
      "Bina Cephe Giydirme",
      "Açıkhava Reklam Baskı"
    ]
  },
  {
    id: "03",
    slug: "isikli-tabela-totem",
    title: "Işıklı / Işıksız Tabela & Totem",
    shortDesc: "Pleksi kutu harf, alüminyum kompozit tabela, totem ve iç mekan yönlendirme levhaları imalatı.",
    badge: "Alüminyum & LED İmalat",
    codeNumber: "03",
    unitPriceEstimate: 1200,
    fullDescription: "Armonitex & UPD Açıkhava bünyesinde alüminyum kompozit, pleksi, paslanmaz krom harf ve yüksek tasarruflu Samsung LED modüller ile kurumunuza özel tabela üretimi gerçekleştirmekteyiz. Tasarımdan CNC kesim, kaynak ve montaj aşamalarına kadar tüm süreç fabrika bünyemizde tamamlanır.",
    features: [
      "Alüminyum ve Pleksi Kutu Harf CNC Kesim Teknolojisi",
      "IP67 Su Geçirmez Modül LED Aydınlatma (Düşük Enerji Tüketimi)",
      "Statik Fırın Boyalı Paslanmaz Konstrüksiyon",
      "İç ve Dış Mekan Yönlendirme Levha Kİtleri"
    ],
    specifications: [
      { label: "Aydınlatma Tipi", value: "IP67 LED Modül (50.000 Saat Ömür)" },
      { label: "Gövde Malzemesi", value: "4mm Alüminyum Kompozit Paneller" },
      { label: "Garanti Süresi", value: "2 Yıl Birebir Tesis Garantisi" },
      { label: "Üretim Süresi", value: "3 - 7 İş Günü" }
    ],
    faqs: [
      {
        question: "Tabela LED aydınlatması ne kadar elektrik harcar?",
        answer: "Kullandığımız yeni nesil IP67 LED modüller geleneksel floresan sistemlere göre %75 daha az elektrik tüketir."
      }
    ],
    seoKeywords: [
      "Işıklı Tabela İmalatı",
      "Pleksi Kutu Harf",
      "Alüminyum Kompozit Tabela",
      "Totem Tabela Ümraniye",
      "Tabela Fiyatları İstanbul"
    ]
  },
  {
    id: "04",
    slug: "arac-cephe-giydirme",
    title: "Araç & Cephe Giydirme",
    shortDesc: "Ticari filo araç kaplama, One Way Vision delikli folyo ve cam/bina cephe grafik uygulamaları.",
    badge: "Filo & Cephe Grafiği",
    codeNumber: "04",
    unitPriceEstimate: 350,
    fullDescription: "Şirket ticari araçlarınız ve bina cam cepheleriniz için cast folyo ve One Way Vision (delikli cam folyosu) malzemeleri ile profesyonel kaplama hizmeti veriyoruz. Tesisimizdeki ısı korumalı giydirme alanında uzman ustalarımız tarafından sıfır hava kabarcığı ile uygulama tamamlanır.",
    features: [
      "Esnek Cast Folyo (Araç Kıvrımlarına Tam Uyum)",
      "One Way Vision (İçeriden Dışarısı Görünür, Dışarıdan İse Reklam)",
      "Araç Boyasına Zarar Vermeyen Alman Menşeili Yapışkanlı Malzeme",
      "Muayene ve Ruhsat Uyumlu Reklam Projelendirme"
    ],
    specifications: [
      { label: "Folyo Türü", value: "Cast Folyo & One Way Vision" },
      { label: "Söküm Kolaylığı", value: "İz Bırakmadan Sıcak Hava ile Söküm" },
      { label: "Ömür", value: "3-5 Yıl Dış Koşul Dayanımı" },
      { label: "Uygulama Alanı", value: "Kapalı Tesisimizde İklimlendirilmiş Garaj" }
    ],
    faqs: [
      {
        question: "Araç giydirme araç boyasına zarar verir mi?",
        answer: "Hayır. Kaliteli cast folyolarımız orijinal araç boyasını dış etkenlerden, çiziklerden ve güneş solmasından korur."
      }
    ],
    seoKeywords: [
      "Araç Giydirme İstanbul",
      "Filo Araç Kaplama",
      "One Way Vision Baskı",
      "Cam Cephe Giydirme",
      "Araç Reklam Giydirme"
    ]
  },
  {
    id: "05",
    slug: "display-sistemleri",
    title: "Display Sistemleri & Stand",
    shortDesc: "Roll-up stand, örümcek (popup) stand, plaj bayrağı ve fuar sergileme panoları imalatı.",
    badge: "Modüler Alüminyum Gövde",
    codeNumber: "05",
    unitPriceEstimate: 450,
    fullDescription: "Fuar, lansman, seminer ve Mağaza içi etkinlikleriniz için kolay kurulup taşınabilir Roll-up mekanizmaları, örümcek standlar ve plaj bayrakları üretiyoruz. Alüminyum gövdeli, taşıma çantalı ve yeniden baskı değişimi yapılabilir modüler mekanizmalar sunulmaktadır.",
    features: [
      "Hafif ve Dayanıklı Eloksallı Alüminyum Mekanizma",
      "Kıvrılmayan (Anti-Curl) Özel Roll-up Vinil Baskısı",
      "Özel Taşıma Çantası İle Birlikte Teslimat",
      "Görsel Değişimi İmkanı (Mekanizma Yeniden Kullanılabilir)"
    ],
    specifications: [
      { label: "Ölçü Seçenekleri", value: "85x200cm, 100x200cm, 120x200cm, 3x4m Örümcek" },
      { label: "Kurulum Süresi", value: "30 Saniye (Aletsiz Kolay Kurulum)" },
      { label: "Koli İçeriği", value: "Alüminyum Gövde + Özel Çanta + Baskı" },
      { label: "Teslimat", value: "Aynı Gün Teslimat İmkanı" }
    ],
    faqs: [
      {
        question: "Roll-up stand baskısı zamanla kenarlardan kıvrılır mı?",
        answer: "Hayır. Kullandığımız özel Anti-Curl (kıvrılma önleyici) gri arkalı film malzemesi sayesinde Roll-up görselleriniz yıllarca düz kalır."
      }
    ],
    seoKeywords: [
      "Roll-up Stand Fiyatları",
      "Örümcek Stand İmalatı",
      "Plaj Bayrağı Baskı",
      "Fuar Display Sistemleri",
      "Display Stand İstanbul"
    ]
  }
];

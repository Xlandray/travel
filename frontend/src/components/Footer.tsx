import Link from "next/link";
import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="bg-white-token text-subtle-token pt-16 pb-12 border-t border-token">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-token">
          {/* Brand Info */}
          <div className="space-y-4 md:col-span-1">
            <div className="py-1">
              <Logo className="w-full max-w-[240px] sm:max-w-[350px] h-[72px] sm:h-[100px]" />
            </div>
            <p className="text-sm text-muted-token leading-relaxed">
              Çorlu çıkışlı günübirlik ve konaklamalı tur organizasyonlarında güvenli stok garantisi ve konforlu seyahat hizmetleri.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-main-token font-bold text-xs tracking-wider uppercase mb-4">Hızlı Bağlantılar</h4>
            <ul className="space-y-2 text-sm text-subtle-token">
              <li>
                <Link href="/turlar" className="hover:text-teal-400 transition-colors">Tüm Turlar</Link>
              </li>
              <li>
                <Link href="/turlar?tip=gunubirlik" className="hover:text-teal-400 transition-colors">Günübirlik Turlar</Link>
              </li>
              <li>
                <Link href="/auth/login" className="hover:text-teal-400 transition-colors">Acente Girişi (B2B)</Link>
              </li>
              <li>
                <Link href="/iletisim" className="hover:text-teal-400 transition-colors">İletişim &amp; Destek</Link>
              </li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h4 className="text-main-token font-bold text-xs tracking-wider uppercase mb-4">Kalkış Noktaları</h4>
            <ul className="space-y-2 text-sm text-subtle-token">
              <li>📍 Çorlu Merkez (Heykel Önü)</li>
              <li>📍 Orion AVM Önü Duraklar</li>
              <li>🚌 Özel Grup Tur Transferleri</li>
              <li>🔒 Canlı Stok Kilitleme Teknolojisi</li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="space-y-2">
            <h4 className="text-main-token font-bold text-xs tracking-wider uppercase mb-4">İletişim &amp; Acente</h4>
            <p className="text-sm text-subtle-token leading-snug">
              📍 Salih Omurtak Cd. No:45, Çorlu / Tekirdağ
            </p>
            <p className="text-sm text-subtle-token pt-1">
              ✉️ destek@corlutravel.com.tr
            </p>
            <p className="text-sm text-brand-token font-mono font-bold pt-1">
              📞 0 (282) 650 00 00
            </p>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-muted-token">
          <p>© {new Date().getFullYear()} Çorlu Travel (Armonitex Seyahat Sistemleri). Tüm hakları saklıdır.</p>
          <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 sm:mt-0 justify-center sm:justify-end">
            <a href="#" className="hover:text-main-token transition-colors">Gizlilik Politikası</a>
            <a href="#" className="hover:text-main-token transition-colors">Kullanım Şartları</a>
            <a href="#" className="hover:text-main-token transition-colors">KVKK Aydınlatma</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

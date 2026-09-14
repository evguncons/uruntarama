import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hedef AVM | AI Destekli Ürün Piyasa Araştırması ve Satılabilirlik Radarı',
  description:
    'Hedef AVM için ürün fotoğraflarını tarayarak Türkiye perakende pazar analizi, elden senetli ve peşin fiyat stratejisi, satılabilirlik puanı ve kampanya fizibilitesi sunan kurumsal AI yazılımı.',
  icons: {
    icon: '/favicon.ico'
  }
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#0f172a'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className="dark scroll-smooth">
      <body className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-rose-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}

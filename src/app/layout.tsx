import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hedef AVM | AI Ürün Piyasa Araştırması ve Satılabilirlik Radarı',
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
  themeColor: '#ffffff'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className="scroll-smooth">
      <body className="min-h-screen bg-[#faf5f8] text-slate-900 font-sans antialiased selection:bg-fuchsia-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}

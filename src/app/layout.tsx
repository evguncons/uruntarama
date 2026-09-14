import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hedef AVM | AI Ürün Piyasa Araştırması ve Satılabilirlik Radarı',
  description:
    'Hedef Alışveriş Merkezleri - Evinizin Rengi. Ürün fotoğraflarını tarayarak piyasa analizi, elden senetli taksit stratejisi ve satılabilirlik fizibilitesi sunan kurumsal AI yazılımı.',
  icons: {
    icon: '/hedef-logo.png',
    apple: '/hedef-logo.png'
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
      <body className="min-h-screen bg-[#faf5f8] text-slate-900 font-sans antialiased selection:bg-[#c81373] selection:text-white">
        {children}
      </body>
    </html>
  );
}

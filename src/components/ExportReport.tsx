'use client';

import React, { useState } from 'react';
import { Download, Share2, Copy, Check, MessageSquare } from 'lucide-react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { ProductAnalysis } from '@/lib/types';

interface ExportReportProps {
  analysis: ProductAnalysis;
  targetElementId: string;
}

export const ExportReport: React.FC<ExportReportProps> = ({
  analysis,
  targetElementId,
}) => {
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [copied, setCopied] = useState(false);

  // WhatsApp ve Pano metnini hazırla
  const generateShareText = () => {
    return `🎯 *HEDEF AVM - AI ÜRÜN PİYASA ARAŞTIRMASI*
━━━━━━━━━━━━━━━━━━━━━━
📦 *Ürün:* ${analysis.productName}
🏷️ *Marka:* ${analysis.brand} | *Kategori:* ${analysis.category}
${analysis.barcode ? `🔢 *Barkod:* ${analysis.barcode}\n` : ''}
📊 *Fizibilite Kararı:* ${analysis.feasibility.verdict} (${analysis.feasibility.score}/100 Puan)
💡 *Özet:* ${analysis.feasibility.headline}

💰 *PİYASA FİYATLARI:*
• Piyasa Ortalaması: ${analysis.marketPrices.average.toLocaleString('tr-TR')} ₺
• Min - Max Aralığı: ${analysis.marketPrices.min.toLocaleString('tr-TR')} ₺ - ${analysis.marketPrices.max.toLocaleString('tr-TR')} ₺

🏪 *HEDEF AVM TAVSİYE FİYATLARI:*
• Peşin / Tek Çekim: ${analysis.hedefPricing.cashRecommendedPrice.toLocaleString('tr-TR')} ₺
• Elden Senetli (12 Ay): ${analysis.hedefPricing.installmentRecommendedPrice.toLocaleString('tr-TR')} ₺
• Aylık Taksit: ${analysis.hedefPricing.monthlyInstallmentPrice.toLocaleString('tr-TR')} ₺ x ${analysis.hedefPricing.installmentCount} Ay

✅ *Neden Satar:*
${analysis.feasibility.reasonsToSell.map((r) => `• ${r}`).join('\n')}

⚠️ *Riskler & Notlar:*
${analysis.feasibility.risksAndWatchouts.map((r) => `• ${r}`).join('\n')}

📅 *Tarih:* ${new Date(analysis.createdAt).toLocaleDateString('tr-TR')}`;
  };

  // PDF İndirme
  const handleDownloadPdf = async () => {
    try {
      setIsGeneratingPdf(true);
      const element = document.getElementById(targetElementId);
      if (!element) {
        alert('Rapor alanı bulunamadı.');
        return;
      }

      // html2canvas ile yüksek kaliteli ekran görüntüsü al
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#0f172a',
        logging: false
      });

      const imgData = canvas.toDataURL('image/jpeg', 0.95);
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      let position = 0;
      let heightLeft = pdfHeight;
      const pageHeight = pdf.internal.pageSize.getHeight();

      // Çoklu sayfa desteği
      pdf.addImage(imgData, 'JPEG', 0, position, pdfWidth, pdfHeight);
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - pdfHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'JPEG', 0, position, pdfWidth, pdfHeight);
        heightLeft -= pageHeight;
      }

      const fileName = `Hedef_AVM_Piyasa_Raporu_${analysis.brand}_${analysis.productName.substring(0, 15).replace(/\s+/g, '_')}.pdf`;
      pdf.save(fileName);
    } catch (err) {
      console.error('PDF oluşturma hatası:', err);
      alert('PDF oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // WhatsApp ile paylaş
  const handleShareWhatsApp = () => {
    const text = encodeURIComponent(generateShareText());
    window.open(`https://api.whatsapp.com/send?text=${text}`, '_blank');
  };

  // Panoya Kopyala
  const handleCopyText = async () => {
    try {
      await navigator.clipboard.writeText(generateShareText());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
      {/* PDF İndir */}
      <button
        onClick={handleDownloadPdf}
        disabled={isGeneratingPdf}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs sm:text-sm font-semibold border border-slate-700 transition active:scale-95 disabled:opacity-50 shadow-sm"
      >
        <Download className="w-4 h-4 text-rose-400" />
        <span>{isGeneratingPdf ? 'PDF Hazırlanıyor...' : 'PDF Rapor İndir'}</span>
      </button>

      {/* WhatsApp Paylaş */}
      <button
        onClick={handleShareWhatsApp}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white text-xs sm:text-sm font-semibold transition active:scale-95 shadow-sm"
      >
        <MessageSquare className="w-4 h-4" />
        <span>WhatsApp Paylaş</span>
      </button>

      {/* Panoya Kopyala */}
      <button
        onClick={handleCopyText}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-medium border border-slate-700 transition active:scale-95 shadow-sm"
      >
        {copied ? (
          <>
            <Check className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400">Kopyalandı!</span>
          </>
        ) : (
          <>
            <Copy className="w-4 h-4" />
            <span>Özeti Kopyala</span>
          </>
        )}
      </button>
    </div>
  );
};

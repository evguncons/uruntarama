'use client';

import React from 'react';
import {
  Tag,
  Building2,
  Barcode,
  Layers,
  CheckCircle,
  AlertTriangle,
  Flame,
  CreditCard,
  ShoppingBag,
  Megaphone,
  Store,
  Users,
  Calendar,
  Sparkles,
  ArrowUpRight
} from 'lucide-react';
import { ProductAnalysis } from '@/lib/types';
import { ScoreMeter } from './ScoreMeter';
import { CostSimulator } from './CostSimulator';
import { ExportReport } from './ExportReport';

interface AnalysisResultProps {
  analysis: ProductAnalysis;
  onNewScan: () => void;
}

export const AnalysisResult: React.FC<AnalysisResultProps> = ({
  analysis,
  onNewScan
}) => {
  return (
    <div className="w-full space-y-6 pb-12">
      {/* Üst Eylem Çubuğu & Dışa Aktarma */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <div>
          <span className="text-xs text-rose-400 font-bold uppercase tracking-wider block">
            Analiz Raporu Hazır
          </span>
          <h2 className="text-lg sm:text-xl font-black text-white">
            {analysis.productName}
          </h2>
          <span className="text-xs text-slate-400">
            Tarih: {new Date(analysis.createdAt).toLocaleString('tr-TR')}
          </span>
        </div>

        <ExportReport analysis={analysis} targetElementId="printable-analysis-report" />
      </div>

      {/* Rapor Konteyneri (PDF çıktısı bu ID üzerinden alınır) */}
      <div
        id="printable-analysis-report"
        className="space-y-6 bg-slate-950 p-2 sm:p-4 rounded-3xl"
      >
        {/* 1. Ürün Kimlik Kartı */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            {analysis.imagePreview && (
              <div className="w-full md:w-48 h-48 rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shrink-0 flex items-center justify-center p-2">
                <img
                  src={analysis.imagePreview}
                  alt={analysis.productName}
                  className="w-full h-full object-contain"
                />
              </div>
            )}

            <div className="flex-1 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-bold flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5" />
                  {analysis.brand}
                </span>

                <span className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-slate-400" />
                  {analysis.category}
                </span>

                {analysis.modelOrCode && (
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-xs font-mono">
                    Model: {analysis.modelOrCode}
                  </span>
                )}

                {analysis.barcode && (
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-xs font-mono flex items-center gap-1">
                    <Barcode className="w-3.5 h-3.5 text-slate-400" />
                    {analysis.barcode}
                  </span>
                )}
              </div>

              <h1 className="text-xl sm:text-2xl font-black text-white leading-snug">
                {analysis.productName}
              </h1>

              {/* Temel Özellik Rozetleri */}
              {analysis.keyFeatures.length > 0 && (
                <div className="pt-2">
                  <span className="text-[11px] uppercase font-bold text-slate-400 block mb-1.5">
                    Tespit Edilen Önemli Nitelikler:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.keyFeatures.map((feat, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800 text-slate-300 text-xs flex items-center gap-1.5"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                        {feat}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 2. Satılabilirlik Skoru & Karar Motoru */}
        <ScoreMeter feasibility={analysis.feasibility} />

        {/* 3. Piyasa Fiyatları ve Hedef AVM Fiyat Stratejisi */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Piyasa Fiyat Dağılımı */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <Store className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">
                      Türkiye Piyasa Fiyat Dağılımı
                    </h3>
                    <p className="text-xs text-slate-400">
                      Pazaryerleri ve zincir mağaza fiyat aralığı
                    </p>
                  </div>
                </div>
              </div>

              {/* Fiyat Göstergeleri */}
              <div className="grid grid-cols-3 gap-3 mb-5 text-center">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    En Düşük
                  </span>
                  <span className="text-base sm:text-lg font-bold text-slate-300">
                    {analysis.marketPrices.min.toLocaleString('tr-TR')} ₺
                  </span>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-blue-500/30 ring-1 ring-blue-500/20">
                  <span className="text-[10px] uppercase font-bold text-blue-400 block">
                    Piyasa Ortalaması
                  </span>
                  <span className="text-base sm:text-lg font-black text-blue-300">
                    {analysis.marketPrices.average.toLocaleString('tr-TR')} ₺
                  </span>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    En Yüksek
                  </span>
                  <span className="text-base sm:text-lg font-bold text-slate-300">
                    {analysis.marketPrices.max.toLocaleString('tr-TR')} ₺
                  </span>
                </div>
              </div>

              {/* Rakip Karşılaştırma Listesi */}
              <div className="space-y-2">
                <span className="text-[11px] uppercase font-bold text-slate-400 block">
                  Platform Örnekleri:
                </span>
                {analysis.competitorBenchmarks.map((comp, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs"
                  >
                    <div>
                      <span className="font-semibold text-white block">
                        {comp.platform}
                      </span>
                      {comp.notes && (
                        <span className="text-[11px] text-slate-400">
                          {comp.notes}
                        </span>
                      )}
                    </div>
                    <span className="font-bold text-slate-200 text-sm">
                      {comp.estimatedPrice.toLocaleString('tr-TR')} ₺
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Hedef AVM Özel Fiyatlandırma & Taksit Stratejisi */}
          <div className="bg-gradient-to-br from-rose-950/20 via-slate-900/90 to-slate-900/90 border border-rose-500/30 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <CreditCard className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">
                      Hedef AVM Fiyat & Senet Stratejisi
                    </h3>
                    <p className="text-xs text-rose-300">
                      Peşin ve elden senetli satış tavsiyesi
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                {/* Peşin Satış Tavsiyesi */}
                <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Peşin / Kredi Kartı Fiyatı
                  </span>
                  <span className="text-xl font-black text-white block mt-1">
                    {analysis.hedefPricing.cashRecommendedPrice.toLocaleString('tr-TR')} ₺
                  </span>
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Online rekabete uyumlu mağaza liste fiyatı
                  </span>
                </div>

                {/* Elden Senetli 12 Taksit */}
                <div className="bg-gradient-to-br from-rose-950/40 to-slate-950 p-3.5 rounded-xl border border-rose-500/40 shadow-inner">
                  <span className="text-[10px] uppercase font-bold text-rose-300 block">
                    Elden Senetli Toplam Satış
                  </span>
                  <span className="text-xl font-black text-rose-200 block mt-1">
                    {analysis.hedefPricing.installmentRecommendedPrice.toLocaleString('tr-TR')} ₺
                  </span>
                  <span className="text-[11px] text-emerald-400 font-semibold mt-1 block">
                    {analysis.hedefPricing.monthlyInstallmentPrice.toLocaleString('tr-TR')} ₺ x {analysis.hedefPricing.installmentCount} Ay Taksit
                  </span>
                </div>
              </div>

              {/* Peşinat Durumu */}
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs flex items-center justify-between mb-3">
                <span className="text-slate-400 font-medium">Tavsiye Peşinat:</span>
                <span className="font-bold text-white">
                  {analysis.hedefPricing.suggestedDownPayment > 0
                    ? `${analysis.hedefPricing.suggestedDownPayment.toLocaleString('tr-TR')} ₺`
                    : 'Peşinatsız Senet (0 ₺ Peşinat)'}
                </span>
              </div>

              {/* Strateji Notu */}
              <div className="p-3 bg-rose-950/30 rounded-xl border border-rose-500/20 text-xs text-slate-200">
                <strong className="text-rose-300 block mb-1">Satın Alma Tavsiyesi:</strong>
                <p className="leading-relaxed text-slate-300">
                  {analysis.hedefPricing.strategyNote}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 4. Kârlılık ve Maliyet Simülatörü */}
        <CostSimulator
          initialCost={analysis.userCost}
          hedefPricing={analysis.hedefPricing}
          marketPrices={analysis.marketPrices}
        />

        {/* 5. Neden Satar? vs Riskler ve Dikkat Edilmesi Gerekenler */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Neden Satar */}
          <div className="bg-slate-900/80 border border-emerald-500/30 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Neden Satar? (Satış Gücü & Fırsatlar)
                </h3>
                <p className="text-xs text-emerald-400">
                  Mağazada hızlı devir ve müşteri çekme nedenleri
                </p>
              </div>
            </div>

            <ul className="space-y-2.5">
              {analysis.feasibility.reasonsToSell.map((reason, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-200 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80"
                >
                  <span className="text-emerald-400 shrink-0 mt-0.5">✓</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Riskler ve Dikkat Edilmesi Gerekenler */}
          <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Riskler ve Dikkat Edilmesi Gerekenler
                </h3>
                <p className="text-xs text-amber-400">
                  Stok fazlası, iade ve fiyat rekabeti uyarıları
                </p>
              </div>
            </div>

            <ul className="space-y-2.5">
              {analysis.feasibility.risksAndWatchouts.map((risk, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-200 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80"
                >
                  <span className="text-amber-400 shrink-0 mt-0.5">!</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 6. Kampanya & Mağaza İçi Pazarlama Kurguları */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Megaphone className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Hedef AVM İçin Özel Kampanya ve Pazarlama Kurguları
              </h3>
              <p className="text-xs text-slate-400">
                Mağaza vitrini, broşür, sosyal medya ve afiş sloganı önerileri
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.campaigns.map((camp, idx) => (
              <div
                key={idx}
                className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-rose-500/40 transition"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      {camp.campaignType}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-white mb-1.5">
                    {camp.title}
                  </h4>

                  <p className="text-xs text-slate-300 leading-relaxed mb-3">
                    {camp.description}
                  </p>
                </div>

                {camp.bannerSlogan && (
                  <div className="mt-2 p-2.5 rounded-lg bg-gradient-to-r from-rose-950/60 to-slate-900 border border-rose-500/20">
                    <span className="text-[10px] uppercase font-bold text-rose-400 block mb-0.5">
                      Afiş & Reklam Sloganı:
                    </span>
                    <span className="text-xs font-semibold text-rose-100 italic block">
                      "{camp.bannerSlogan}"
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 7. Hedef Kitle ve Pazar Notu */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex items-center gap-3 text-xs text-slate-300">
          <Users className="w-5 h-5 text-rose-400 shrink-0" />
          <div>
            <strong className="text-white font-semibold">Hedef Kitle Profili: </strong>
            <span>{analysis.feasibility.targetAudience}</span>
          </div>
        </div>
      </div>

      {/* Alt Aksiyon: Yeni Tarama */}
      <div className="flex justify-center pt-4">
        <button
          onClick={onNewScan}
          className="flex items-center gap-2 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-bold text-sm shadow-xl shadow-rose-900/40 transition active:scale-95"
        >
          <Sparkles className="w-4 h-4" />
          <span>Farklı Bir Ürün Tara</span>
        </button>
      </div>
    </div>
  );
};

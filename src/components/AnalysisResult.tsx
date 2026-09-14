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
  ArrowUpRight,
  TrendingUp
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-4 sm:p-5 rounded-3xl border border-pink-100 shadow-sm">
        <div>
          <span className="text-xs text-fuchsia-700 font-extrabold uppercase tracking-wider block mb-0.5">
            Analiz Raporu Hazır
          </span>
          <h2 className="text-lg sm:text-xl font-black text-slate-900">
            {analysis.productName}
          </h2>
          <span className="text-xs text-slate-400 font-medium">
            Tarih: {new Date(analysis.createdAt).toLocaleString('tr-TR')}
          </span>
        </div>

        <ExportReport analysis={analysis} targetElementId="printable-analysis-report" />
      </div>

      {/* Rapor Konteyneri (PDF çıktısı bu ID üzerinden alınır) */}
      <div
        id="printable-analysis-report"
        className="space-y-6 bg-transparent p-1 sm:p-2 rounded-3xl"
      >
        {/* 1. Ürün Kimlik Kartı */}
        <div className="bg-white border border-pink-100 rounded-3xl p-6 sm:p-7 shadow-xl shadow-fuchsia-950/5">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            {analysis.imagePreview && (
              <div className="w-full md:w-48 h-48 rounded-2xl overflow-hidden bg-slate-50 border border-slate-100 shrink-0 flex items-center justify-center p-3 shadow-inner">
                <img
                  src={analysis.imagePreview}
                  alt={analysis.productName}
                  className="w-full h-full object-contain"
                />
              </div>
            )}

            <div className="flex-1 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-xl bg-fuchsia-50 border border-fuchsia-200 text-fuchsia-700 text-xs font-black flex items-center gap-1.5 shadow-xs">
                  <Building2 className="w-3.5 h-3.5" />
                  {analysis.brand}
                </span>

                <span className="px-3 py-1 rounded-xl bg-slate-100 border border-slate-200 text-slate-700 text-xs font-bold flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-slate-500" />
                  {analysis.category}
                </span>

                {analysis.modelOrCode && (
                  <span className="px-3 py-1 rounded-xl bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono font-semibold">
                    Model: {analysis.modelOrCode}
                  </span>
                )}

                {analysis.barcode && (
                  <span className="px-3 py-1 rounded-xl bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono font-semibold flex items-center gap-1.5">
                    <Barcode className="w-3.5 h-3.5 text-slate-500" />
                    {analysis.barcode}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 leading-snug tracking-tight">
                {analysis.productName}
              </h1>

              {/* Temel Özellik Rozetleri */}
              {analysis.keyFeatures.length > 0 && (
                <div className="pt-2">
                  <span className="text-[11px] uppercase font-bold text-slate-400 block mb-2">
                    Tespit Edilen Önemli Nitelikler:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {analysis.keyFeatures.map((feat, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium flex items-center gap-1.5 shadow-2xs"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-500"></span>
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
          <div className="bg-white border border-pink-100 rounded-3xl p-6 shadow-xl shadow-fuchsia-950/5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-5 pb-4 border-b border-pink-100">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-sky-50 text-sky-600 border border-sky-200">
                    <Store className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-black text-slate-900">
                      Türkiye Piyasa Fiyat Dağılımı
                    </h3>
                    <p className="text-xs text-slate-500 font-medium">
                      Pazaryerleri ve zincir mağaza fiyat skalası
                    </p>
                  </div>
                </div>
              </div>

              {/* Fiyat Göstergeleri */}
              <div className="grid grid-cols-3 gap-3 mb-5 text-center">
                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    En Düşük
                  </span>
                  <span className="text-base sm:text-lg font-black text-slate-800">
                    {analysis.marketPrices.min.toLocaleString('tr-TR')} ₺
                  </span>
                </div>

                <div className="bg-gradient-to-br from-fuchsia-50 to-pink-50 p-3.5 rounded-2xl border border-fuchsia-300 ring-2 ring-fuchsia-500/20 shadow-xs">
                  <span className="text-[10px] uppercase font-black text-fuchsia-700 block">
                    Piyasa Ortalaması
                  </span>
                  <span className="text-base sm:text-lg font-black text-fuchsia-900">
                    {analysis.marketPrices.average.toLocaleString('tr-TR')} ₺
                  </span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    En Yüksek
                  </span>
                  <span className="text-base sm:text-lg font-black text-slate-800">
                    {analysis.marketPrices.max.toLocaleString('tr-TR')} ₺
                  </span>
                </div>
              </div>

              {/* Rakip Karşılaştırma Listesi */}
              <div className="space-y-2">
                <span className="text-[11px] uppercase font-bold text-slate-400 block mb-1">
                  Platform Örnekleri:
                </span>
                {analysis.competitorBenchmarks.map((comp, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs"
                  >
                    <div>
                      <span className="font-bold text-slate-800 block">
                        {comp.platform}
                      </span>
                      {comp.notes && (
                        <span className="text-[11px] text-slate-500 font-medium">
                          {comp.notes}
                        </span>
                      )}
                    </div>
                    <span className="font-black text-slate-900 text-sm">
                      {comp.estimatedPrice.toLocaleString('tr-TR')} ₺
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Hedef AVM Özel Fiyatlandırma & Taksit Stratejisi */}
          <div className="bg-gradient-to-br from-fuchsia-50/80 via-pink-50/40 to-white border border-fuchsia-200 rounded-3xl p-6 shadow-xl shadow-fuchsia-950/5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-5 pb-4 border-b border-fuchsia-200/80">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-fuchsia-600 text-white shadow-md shadow-fuchsia-600/30">
                    <CreditCard className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-black text-slate-900">
                      Hedef AVM Fiyat & Senet Stratejisi
                    </h3>
                    <p className="text-xs text-fuchsia-700 font-semibold">
                      Peşin ve elden senetli taksitli satış tavsiyesi
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                {/* Peşin Satış Tavsiyesi */}
                <div className="bg-white/90 p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Peşin / Kredi Kartı Fiyatı
                  </span>
                  <span className="text-2xl font-black text-slate-900 block mt-1">
                    {analysis.hedefPricing.cashRecommendedPrice.toLocaleString('tr-TR')} ₺
                  </span>
                  <span className="text-[11px] text-slate-500 mt-1 block font-medium">
                    Online rekabete uyumlu liste fiyatı
                  </span>
                </div>

                {/* Elden Senetli 12 Taksit */}
                <div className="bg-gradient-to-br from-fuchsia-600 via-rose-600 to-pink-600 text-white p-4 rounded-2xl shadow-lg shadow-fuchsia-600/20">
                  <span className="text-[10px] uppercase font-black text-pink-100 block">
                    Elden Senetli Toplam Satış
                  </span>
                  <span className="text-2xl font-black text-white block mt-1">
                    {analysis.hedefPricing.installmentRecommendedPrice.toLocaleString('tr-TR')} ₺
                  </span>
                  <span className="text-xs font-bold text-pink-100 mt-1 block">
                    {analysis.hedefPricing.monthlyInstallmentPrice.toLocaleString('tr-TR')} ₺ x {analysis.hedefPricing.installmentCount} Ay Taksit
                  </span>
                </div>
              </div>

              {/* Peşinat Durumu */}
              <div className="p-3.5 bg-white/90 rounded-2xl border border-fuchsia-200/80 text-xs flex items-center justify-between mb-3 shadow-2xs">
                <span className="text-slate-600 font-bold">Tavsiye Peşinat:</span>
                <span className="font-black text-fuchsia-800 text-sm">
                  {analysis.hedefPricing.suggestedDownPayment > 0
                    ? `${analysis.hedefPricing.suggestedDownPayment.toLocaleString('tr-TR')} ₺`
                    : 'Peşinatsız Senet (0 ₺ Peşinat)'}
                </span>
              </div>

              {/* Strateji Notu */}
              <div className="p-3.5 bg-fuchsia-100/60 rounded-2xl border border-fuchsia-200 text-xs text-slate-800">
                <strong className="text-fuchsia-900 block mb-1 font-bold">Satın Alma Tavsiyesi:</strong>
                <p className="leading-relaxed text-slate-700 font-medium">
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
          <div className="bg-white border border-emerald-200 rounded-3xl p-6 shadow-xl shadow-emerald-950/5">
            <div className="flex items-center gap-3 mb-4 pb-3 border-b border-emerald-100">
              <div className="p-2.5 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-black text-slate-900">
                  Neden Satar? (Satış Gücü & Fırsatlar)
                </h3>
                <p className="text-xs text-emerald-700 font-medium">
                  Mağazada hızlı devir ve müşteri çekme nedenleri
                </p>
              </div>
            </div>

            <ul className="space-y-2.5">
              {analysis.feasibility.reasonsToSell.map((reason, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-3 text-xs sm:text-sm text-slate-800 bg-emerald-50/50 p-3 rounded-2xl border border-emerald-100 font-medium leading-relaxed"
                >
                  <span className="text-emerald-600 font-black shrink-0 mt-0.5">✓</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Riskler ve Dikkat Edilmesi Gerekenler */}
          <div className="bg-white border border-amber-200 rounded-3xl p-6 shadow-xl shadow-amber-950/5">
            <div className="flex items-center gap-3 mb-4 pb-3 border-b border-amber-100">
              <div className="p-2.5 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-black text-slate-900">
                  Riskler ve Dikkat Edilmesi Gerekenler
                </h3>
                <p className="text-xs text-amber-700 font-medium">
                  Stok fazlası, iade ve fiyat rekabeti uyarıları
                </p>
              </div>
            </div>

            <ul className="space-y-2.5">
              {analysis.feasibility.risksAndWatchouts.map((risk, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-3 text-xs sm:text-sm text-slate-800 bg-amber-50/50 p-3 rounded-2xl border border-amber-100 font-medium leading-relaxed"
                >
                  <span className="text-amber-600 font-black shrink-0 mt-0.5">!</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 6. Kampanya & Mağaza İçi Pazarlama Kurguları */}
        <div className="bg-white border border-pink-100 rounded-3xl p-6 sm:p-7 shadow-xl shadow-fuchsia-950/5">
          <div className="flex items-center gap-3 mb-5 pb-4 border-b border-pink-100">
            <div className="p-2.5 rounded-2xl bg-fuchsia-50 text-fuchsia-600 border border-fuchsia-200">
              <Megaphone className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-black text-slate-900">
                Hedef AVM İçin Özel Kampanya ve Pazarlama Kurguları
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                Mağaza vitrini, çeyiz broşürü ve reklam sloganı önerileri
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.campaigns.map((camp, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-b from-pink-50/20 to-white border border-pink-100 rounded-2xl p-5 flex flex-col justify-between hover:border-fuchsia-300 hover:shadow-md transition"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-fuchsia-100 text-fuchsia-800 border border-fuchsia-200">
                      {camp.campaignType}
                    </span>
                  </div>

                  <h4 className="text-sm font-black text-slate-900 mb-2">
                    {camp.title}
                  </h4>

                  <p className="text-xs text-slate-600 leading-relaxed mb-3 font-medium">
                    {camp.description}
                  </p>
                </div>

                {camp.bannerSlogan && (
                  <div className="mt-2 p-3 rounded-xl bg-gradient-to-r from-fuchsia-50 via-pink-50 to-rose-50 border border-fuchsia-200 shadow-2xs">
                    <span className="text-[10px] uppercase font-bold text-fuchsia-700 block mb-0.5">
                      Afiş & Reklam Sloganı:
                    </span>
                    <span className="text-xs font-bold text-fuchsia-900 italic block">
                      "{camp.bannerSlogan}"
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 7. Hedef Kitle ve Pazar Notu */}
        <div className="bg-white border border-pink-100 rounded-2xl p-4 flex items-center gap-3 text-xs text-slate-700 shadow-xs">
          <Users className="w-5 h-5 text-fuchsia-600 shrink-0" />
          <div>
            <strong className="text-slate-900 font-bold">Hedef Kitle Profili: </strong>
            <span className="font-medium">{analysis.feasibility.targetAudience}</span>
          </div>
        </div>
      </div>

      {/* Alt Aksiyon: Yeni Tarama */}
      <div className="flex justify-center pt-4">
        <button
          onClick={onNewScan}
          className="flex items-center gap-2 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-fuchsia-600 via-rose-600 to-pink-600 hover:from-fuchsia-500 hover:to-pink-500 text-white font-black text-sm shadow-xl shadow-fuchsia-600/30 transition active:scale-95"
        >
          <Sparkles className="w-4 h-4" />
          <span>Farklı Bir Ürün Tara</span>
        </button>
      </div>
    </div>
  );
};

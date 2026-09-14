'use client';

import React, { useState } from 'react';
import { Calculator, TrendingUp, DollarSign, Percent, ArrowRight, Wallet } from 'lucide-react';
import { HedefAvmPricingStrategy, MarketPriceRange } from '@/lib/types';

interface CostSimulatorProps {
  initialCost?: number;
  hedefPricing: HedefAvmPricingStrategy;
  marketPrices: MarketPriceRange;
}

export const CostSimulator: React.FC<CostSimulatorProps> = ({
  initialCost,
  hedefPricing,
  marketPrices
}) => {
  const [cost, setCost] = useState<number | ''>(
    initialCost || (hedefPricing.cashRecommendedPrice ? Math.round(hedefPricing.cashRecommendedPrice * 0.65) : 1000)
  );

  const numericCost = Number(cost) || 0;

  // Peşin hesaplamaları
  const cashPrice = hedefPricing.cashRecommendedPrice || marketPrices.average;
  const cashProfit = numericCost > 0 ? cashPrice - numericCost : 0;
  const cashMarginPercent = cashPrice > 0 && numericCost > 0 ? Math.round((cashProfit / cashPrice) * 100) : 0;

  // Elden Senetli / Taksitli hesaplamaları
  const installmentPrice = hedefPricing.installmentRecommendedPrice || Math.round(cashPrice * 1.3);
  const installmentProfit = numericCost > 0 ? installmentPrice - numericCost : 0;
  const installmentMarginPercent =
    installmentPrice > 0 && numericCost > 0 ? Math.round((installmentProfit / installmentPrice) * 100) : 0;

  return (
    <div className="bg-white border border-pink-100/90 rounded-3xl p-6 shadow-xl shadow-fuchsia-950/5">
      <div className="flex items-center justify-between gap-3 mb-5 pb-4 border-b border-pink-100">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-fuchsia-50 text-fuchsia-600 border border-fuchsia-200">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-black text-slate-900">
              Hedef AVM Kârlılık ve Marj Simülatörü
            </h4>
            <p className="text-xs text-slate-500 font-medium">
              Ürünün tedarik alış maliyetini girin, net kârı ve senetli getirisini anında görün.
            </p>
          </div>
        </div>
      </div>

      {/* Girdi Alanı */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">
            Tedarikçi Alış Fiyatı (₺)
          </label>
          <div className="relative">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-fuchsia-600 font-black text-sm">
              ₺
            </span>
            <input
              type="number"
              min="0"
              value={cost}
              onChange={(e) => setCost(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder="Örn: 2500"
              className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-200 focus:border-fuchsia-500 focus:bg-white focus:ring-2 focus:ring-fuchsia-500/20 rounded-2xl text-slate-900 font-bold text-sm outline-none transition"
            />
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block font-medium">
            Fatura altı net ürün geliş maliyeti
          </span>
        </div>

        {/* Peşin Satış Getirisi */}
        <div className="bg-slate-50 border border-slate-200/80 p-4 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-600">Peşin / Kredi Kartı</span>
            <span className="text-xs font-black text-slate-900">
              {cashPrice.toLocaleString('tr-TR')} ₺
            </span>
          </div>

          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Brüt Kâr
              </span>
              <span
                className={`text-lg font-black ${
                  cashProfit >= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {cashProfit >= 0 ? '+' : ''}
                {cashProfit.toLocaleString('tr-TR')} ₺
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Kâr Marjı
              </span>
              <span
                className={`text-xs font-black px-2.5 py-1 rounded-lg ${
                  cashMarginPercent >= 25
                    ? 'bg-emerald-100 text-emerald-800'
                    : cashMarginPercent >= 10
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                %{cashMarginPercent}
              </span>
            </div>
          </div>
        </div>

        {/* Elden Senetli / 12 Ay Getirisi */}
        <div className="bg-gradient-to-br from-fuchsia-50/80 via-pink-50/40 to-white border border-fuchsia-200 p-4 rounded-2xl flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-fuchsia-700">
              Elden Senetli (12 Taksit)
            </span>
            <span className="text-xs font-black text-fuchsia-900">
              {installmentPrice.toLocaleString('tr-TR')} ₺
            </span>
          </div>

          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                Vadeli Toplam Kâr
              </span>
              <span
                className={`text-lg font-black ${
                  installmentProfit >= 0 ? 'text-fuchsia-700' : 'text-rose-600'
                }`}
              >
                +{installmentProfit.toLocaleString('tr-TR')} ₺
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                Taksitli Marj
              </span>
              <span className="text-xs font-black px-2.5 py-1 rounded-lg bg-fuchsia-200/70 text-fuchsia-800">
                %{installmentMarginPercent}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Değerlendirme Çubuğu */}
      {numericCost > 0 && (
        <div className="bg-slate-50/90 p-3.5 rounded-2xl border border-slate-200/80 text-xs flex items-center justify-between flex-wrap gap-2 text-slate-700 font-medium">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-fuchsia-600 shrink-0" />
            <span>
              <strong className="font-bold text-slate-900">Finansal Yorum:</strong>{' '}
              {cashMarginPercent >= 30
                ? 'Hedef AVM mağaza kâr hedeflerinin üzerinde, son derece kârlı bir ürün grubu.'
                : cashMarginPercent >= 18
                ? 'Perakende standartlarında dengeli ve sağlıklı bir marja sahip.'
                : 'Peşin kâr marjı zayıf, bu üründe hacim veya elden taksitli paketleme şart.'}
            </span>
          </div>
          <span className="text-xs text-fuchsia-700 font-bold bg-fuchsia-50 px-2.5 py-1 rounded-lg border border-fuchsia-200">
            Aylık: {Math.round(installmentPrice / 12).toLocaleString('tr-TR')} ₺ x 12 Ay
          </span>
        </div>
      )}
    </div>
  );
};

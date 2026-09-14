'use client';

import React, { useState } from 'react';
import { Calculator, TrendingUp, DollarSign, Percent, ArrowRight } from 'lucide-react';
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
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg">
      <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-bold text-white">
              Hedef AVM Kârlılık ve Marj Simülatörü
            </h4>
            <p className="text-xs text-slate-400">
              Ürünün tedarik alış fiyatını girin, net kârlılığı ve senetli getirisini anında görün.
            </p>
          </div>
        </div>
      </div>

      {/* Girdi Alanı */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Tedarikçi Alış Fiyatı (₺)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm">
              ₺
            </span>
            <input
              type="number"
              min="0"
              value={cost}
              onChange={(e) => setCost(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder="Örn: 2500"
              className="w-full pl-8 pr-3 py-2 bg-slate-950 border border-slate-700 focus:border-rose-500 focus:ring-1 focus:ring-rose-500 rounded-xl text-white font-semibold text-sm outline-none transition"
            />
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Fatura altı net geliş maliyeti
          </span>
        </div>

        {/* Peşin Satış Getirisi */}
        <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Peşin / Kredi Kartı</span>
            <span className="text-xs font-bold text-slate-200">
              {cashPrice.toLocaleString('tr-TR')} ₺
            </span>
          </div>

          <div className="mt-2 flex items-baseline justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                Brüt Kâr
              </span>
              <span
                className={`text-base font-black ${
                  cashProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {cashProfit >= 0 ? '+' : ''}
                {cashProfit.toLocaleString('tr-TR')} ₺
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                Kâr Marjı
              </span>
              <span
                className={`text-sm font-black px-2 py-0.5 rounded ${
                  cashMarginPercent >= 25
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : cashMarginPercent >= 10
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-rose-500/20 text-rose-400'
                }`}
              >
                %{cashMarginPercent}
              </span>
            </div>
          </div>
        </div>

        {/* Elden Senetli / 12 Ay Getirisi */}
        <div className="bg-gradient-to-br from-rose-950/30 to-slate-950 border border-rose-500/30 p-3 rounded-xl flex flex-col justify-between shadow-md shadow-rose-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-300">
              Elden Senetli (12 Taksit)
            </span>
            <span className="text-xs font-bold text-rose-100">
              {installmentPrice.toLocaleString('tr-TR')} ₺
            </span>
          </div>

          <div className="mt-2 flex items-baseline justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Vadeli Toplam Kâr
              </span>
              <span
                className={`text-base font-black ${
                  installmentProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                +{installmentProfit.toLocaleString('tr-TR')} ₺
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Taksitli Marj
              </span>
              <span className="text-sm font-black px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                %{installmentMarginPercent}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Değerlendirme Çubuğu */}
      {numericCost > 0 && (
        <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 text-xs flex items-center justify-between flex-wrap gap-2 text-slate-300">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>
              <strong>Finansal Yorum:</strong>{' '}
              {cashMarginPercent >= 30
                ? 'Hedef AVM mağaza marj hedeflerinin üzerinde, son derece kârlı bir ürün grubu.'
                : cashMarginPercent >= 18
                ? 'Perakende standartlarında sağlıklı bir kârlılık potansiyeline sahip.'
                : 'Peşin kâr marjı zayıf, bu üründe hacim veya senetli taksitli paketleme şart.'}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            Aylık Taksit: {Math.round(installmentPrice / 12).toLocaleString('tr-TR')} ₺ x 12 Ay
          </span>
        </div>
      )}
    </div>
  );
};

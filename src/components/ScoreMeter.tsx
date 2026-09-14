'use client';

import React, { useEffect } from 'react';
import confetti from 'canvas-confetti';
import { Award, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { FeasibilityAssessment } from '@/lib/types';

interface ScoreMeterProps {
  feasibility: FeasibilityAssessment;
}

export const ScoreMeter: React.FC<ScoreMeterProps> = ({ feasibility }) => {
  const score = feasibility.score;

  // Skor 80 veya üzeriyse tebrik konfetisi patlat
  useEffect(() => {
    if (score >= 80) {
      try {
        confetti({
          particleCount: 50,
          spread: 60,
          origin: { y: 0.6 }
        });
      } catch (e) {
        // Confetti opsiyoneldir
      }
    }
  }, [score]);

  // Renk ve durum belirleme
  let theme = {
    textColor: 'text-emerald-400',
    borderColor: 'border-emerald-500/40',
    bgGradient: 'from-emerald-950/40 to-slate-900/80',
    barColor: 'bg-emerald-500',
    glow: 'shadow-emerald-500/20',
    icon: CheckCircle2,
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
  };

  if (score < 45) {
    theme = {
      textColor: 'text-rose-400',
      borderColor: 'border-rose-500/40',
      bgGradient: 'from-rose-950/40 to-slate-900/80',
      barColor: 'bg-rose-500',
      glow: 'shadow-rose-500/20',
      icon: XCircle,
      badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/40'
    };
  } else if (score < 70) {
    theme = {
      textColor: 'text-amber-400',
      borderColor: 'border-amber-500/40',
      bgGradient: 'from-amber-950/40 to-slate-900/80',
      barColor: 'bg-amber-500',
      glow: 'shadow-amber-500/20',
      icon: AlertTriangle,
      badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40'
    };
  }

  const IconComponent = theme.icon;

  // Dairesel SVG parametreleri
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div
      className={`relative overflow-hidden rounded-2xl p-5 sm:p-6 bg-gradient-to-br ${theme.bgGradient} border ${theme.borderColor} shadow-xl ${theme.glow} transition-all`}
    >
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
        {/* Sol Taraf: Karar ve Açıklama */}
        <div className="flex-1 text-center sm:text-left">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mb-2">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border ${theme.badgeBg}`}
            >
              <IconComponent className="w-4 h-4" />
              {feasibility.verdict}
            </span>
            <span className="text-xs text-slate-400 font-medium">
              Hedef AVM Fizibilite Kararı
            </span>
          </div>

          <h3 className="text-lg sm:text-xl font-bold text-white mb-2 leading-snug">
            {feasibility.headline}
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-4 pt-4 border-t border-slate-800">
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Piyasa Talebi
              </span>
              <span className="text-xs sm:text-sm font-semibold text-white">
                {feasibility.demandLevel}
              </span>
            </div>

            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Pazar Rekabeti
              </span>
              <span className="text-xs sm:text-sm font-semibold text-white">
                {feasibility.competitionLevel}
              </span>
            </div>

            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                İade Riski
              </span>
              <span className="text-xs sm:text-sm font-semibold text-white">
                {feasibility.returnRisk}
              </span>
            </div>

            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Mevsimsellik
              </span>
              <span className="text-xs sm:text-sm font-semibold text-white truncate block" title={feasibility.seasonalTrend}>
                {feasibility.seasonalTrend}
              </span>
            </div>
          </div>
        </div>

        {/* Sağ Taraf: Dairesel Skor Göstergesi */}
        <div className="relative flex flex-col items-center justify-center shrink-0">
          <div className="relative w-32 h-32 flex items-center justify-center">
            {/* SVG Radial Gauge */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 128 128">
              <circle
                cx="64"
                cy="64"
                r={radius}
                className="stroke-slate-800"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="64"
                cy="64"
                r={radius}
                className={`transition-all duration-1000 ease-out ${
                  score >= 70
                    ? 'stroke-emerald-500'
                    : score >= 45
                    ? 'stroke-amber-500'
                    : 'stroke-rose-500'
                }`}
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>

            {/* İç Merkez Metin */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-3xl sm:text-4xl font-black ${theme.textColor}`}>
                {score}
              </span>
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">
                / 100 PUAN
              </span>
            </div>
          </div>
          <span className="text-xs font-semibold text-slate-300 mt-1">
            Satılabilirlik İndeksi
          </span>
        </div>
      </div>
    </div>
  );
};

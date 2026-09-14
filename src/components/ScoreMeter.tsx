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

  // Renk ve tema belirleme (Açık tema)
  let theme = {
    textColor: 'text-emerald-700',
    borderColor: 'border-emerald-200',
    bgGradient: 'from-emerald-50/80 via-white to-fuchsia-50/40',
    strokeColor: 'stroke-emerald-600',
    icon: CheckCircle2,
    badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300'
  };

  if (score < 45) {
    theme = {
      textColor: 'text-rose-700',
      borderColor: 'border-rose-200',
      bgGradient: 'from-rose-50/80 via-white to-pink-50/40',
      strokeColor: 'stroke-rose-600',
      icon: XCircle,
      badgeBg: 'bg-rose-100 text-rose-800 border-rose-300'
    };
  } else if (score < 75) {
    theme = {
      textColor: 'text-fuchsia-700',
      borderColor: 'border-fuchsia-200',
      bgGradient: 'from-fuchsia-50/80 via-white to-pink-50/40',
      strokeColor: 'stroke-fuchsia-600',
      icon: AlertTriangle,
      badgeBg: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-300'
    };
  }

  const IconComponent = theme.icon;

  // Dairesel SVG parametreleri
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div
      className={`relative overflow-hidden rounded-3xl p-6 sm:p-7 bg-gradient-to-br ${theme.bgGradient} border ${theme.borderColor} shadow-xl shadow-fuchsia-950/5 transition-all`}
    >
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
        {/* Sol Taraf: Karar ve Açıklama */}
        <div className="flex-1 text-center sm:text-left">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mb-2.5">
            <span
              className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-black uppercase tracking-wider border ${theme.badgeBg} shadow-xs`}
            >
              <IconComponent className="w-4 h-4" />
              {feasibility.verdict}
            </span>
            <span className="text-xs text-slate-500 font-semibold">
              Hedef AVM Fizibilite Kararı
            </span>
          </div>

          <h3 className="text-xl sm:text-2xl font-black text-slate-900 mb-2 leading-snug tracking-tight">
            {feasibility.headline}
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-5 border-t border-slate-200/80">
            <div className="bg-white/80 backdrop-blur p-2.5 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Piyasa Talebi
              </span>
              <span className="text-xs sm:text-sm font-black text-slate-800">
                {feasibility.demandLevel}
              </span>
            </div>

            <div className="bg-white/80 backdrop-blur p-2.5 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Pazar Rekabeti
              </span>
              <span className="text-xs sm:text-sm font-black text-slate-800">
                {feasibility.competitionLevel}
              </span>
            </div>

            <div className="bg-white/80 backdrop-blur p-2.5 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                İade Riski
              </span>
              <span className="text-xs sm:text-sm font-black text-slate-800">
                {feasibility.returnRisk}
              </span>
            </div>

            <div className="bg-white/80 backdrop-blur p-2.5 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Mevsimsellik
              </span>
              <span
                className="text-xs sm:text-sm font-black text-slate-800 truncate block"
                title={feasibility.seasonalTrend}
              >
                {feasibility.seasonalTrend}
              </span>
            </div>
          </div>
        </div>

        {/* Sağ Taraf: Dairesel Skor Göstergesi */}
        <div className="relative flex flex-col items-center justify-center shrink-0">
          <div className="relative w-36 h-36 flex items-center justify-center">
            {/* SVG Radial Gauge */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 128 128">
              <circle
                cx="64"
                cy="64"
                r={radius}
                className="stroke-slate-100"
                strokeWidth="11"
                fill="transparent"
              />
              <circle
                cx="64"
                cy="64"
                r={radius}
                className={`transition-all duration-1000 ease-out ${theme.strokeColor}`}
                strokeWidth="11"
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
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-extrabold">
                / 100 PUAN
              </span>
            </div>
          </div>
          <span className="text-xs font-bold text-slate-600 mt-1">
            Satılabilirlik İndeksi
          </span>
        </div>
      </div>
    </div>
  );
};

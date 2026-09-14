'use client';

import React from 'react';
import { Sparkles, History, Zap } from 'lucide-react';

interface HeaderProps {
  onOpenHistory: () => void;
  historyCount: number;
  onNewScan: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenHistory,
  historyCount,
  onNewScan,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-white/95 border-b border-pink-100 shadow-xs transition-colors">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
        {/* Resmi Hedef AVM Logosu */}
        <div
          onClick={onNewScan}
          className="flex items-center gap-3 cursor-pointer group transition-transform active:scale-95"
        >
          <img
            src="/hedef-logo.png"
            alt="Hedef Alışveriş Merkezleri"
            className="h-10 sm:h-12 w-auto object-contain drop-shadow-xs group-hover:scale-105 transition-transform"
          />
          <div className="hidden xs:flex flex-col border-l border-pink-200 pl-3">
            <span className="text-[10px] font-black uppercase tracking-widest text-[#c81373] bg-pink-50 px-2 py-0.5 rounded-md border border-pink-200 inline-block w-fit">
              AI PİYASA RADARI
            </span>
            <span className="text-[10px] text-slate-400 font-semibold mt-0.5">
              Satın Alma & Satılabilirlik Analizi
            </span>
          </div>
        </div>

        {/* Sağ Taraf Butonları */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Gemini AI Aktif Rozeti */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Gemini 2.5 Aktif</span>
          </div>

          {/* Geçmiş Butonu */}
          <button
            onClick={onOpenHistory}
            className="relative flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-pink-50 text-slate-700 text-xs sm:text-sm font-bold transition border border-pink-200 shadow-2xs active:scale-95"
            title="Geçmiş Taramalar"
          >
            <History className="w-4 h-4 text-[#c81373]" />
            <span className="hidden sm:inline">Geçmiş</span>
            {historyCount > 0 && (
              <span className="bg-[#c81373] text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[18px] text-center shadow-xs">
                {historyCount}
              </span>
            )}
          </button>

          {/* Yeni Tarama Butonu */}
          <button
            onClick={onNewScan}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#c81373] via-rose-600 to-pink-600 hover:from-[#b01065] hover:to-rose-500 text-white text-xs sm:text-sm font-black shadow-md shadow-[#c81373]/25 transition active:scale-95"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Yeni Tarama</span>
          </button>
        </div>
      </div>
    </header>
  );
};

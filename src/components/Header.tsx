'use client';

import React from 'react';
import { Sparkles, History, ShoppingBag, Zap } from 'lucide-react';

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
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-white/90 border-b border-pink-100 shadow-sm transition-colors">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div
          onClick={onNewScan}
          className="flex items-center gap-3 cursor-pointer group transition-transform active:scale-95"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-fuchsia-600 via-rose-600 to-pink-500 flex items-center justify-center shadow-md shadow-fuchsia-600/30 group-hover:shadow-fuchsia-600/50 group-hover:scale-105 transition-all">
            <ShoppingBag className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black tracking-wider text-base sm:text-lg bg-clip-text text-transparent bg-gradient-to-r from-fuchsia-700 via-rose-600 to-pink-600">
                HEDEF AVM
              </span>
              <span className="text-[10px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded bg-fuchsia-50 text-fuchsia-700 border border-fuchsia-200">
                AI RADAR
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium hidden xs:block">
              Piyasa İstihbarat & Satılabilirlik Radarı
            </p>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Gemini AI Status Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Gemini 2.5 Aktif</span>
          </div>

          {/* History Button */}
          <button
            onClick={onOpenHistory}
            className="relative flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white hover:bg-pink-50/60 text-slate-700 text-xs sm:text-sm font-semibold transition border border-pink-200/80 shadow-xs active:scale-95"
            title="Geçmiş Taramalar"
          >
            <History className="w-4 h-4 text-fuchsia-600" />
            <span className="hidden sm:inline">Geçmiş</span>
            {historyCount > 0 && (
              <span className="bg-gradient-to-r from-fuchsia-600 to-pink-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[18px] text-center shadow-xs">
                {historyCount}
              </span>
            )}
          </button>

          {/* New Scan Button */}
          <button
            onClick={onNewScan}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-fuchsia-600 via-rose-600 to-pink-600 hover:from-fuchsia-500 hover:to-pink-500 text-white text-xs sm:text-sm font-bold shadow-md shadow-fuchsia-600/25 transition active:scale-95"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Yeni Tarama</span>
          </button>
        </div>
      </div>
    </header>
  );
};

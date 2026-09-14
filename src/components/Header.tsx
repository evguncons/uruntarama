'use client';

import React from 'react';
import { Sparkles, History, ShoppingBag, ShieldCheck } from 'lucide-react';

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
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-slate-900/90 border-b border-slate-800 text-white shadow-lg">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div
          onClick={onNewScan}
          className="flex items-center gap-3 cursor-pointer group transition-transform active:scale-95"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 via-red-600 to-amber-500 flex items-center justify-center shadow-md shadow-rose-600/30 group-hover:shadow-rose-600/50 transition-all">
            <ShoppingBag className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black tracking-wider text-base sm:text-lg bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-rose-200">
                HEDEF AVM
              </span>
              <span className="text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                PRO AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium hidden xs:block">
              Piyasa İstihbarat & Satılabilirlik Radarı
            </p>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Gemini AI Status Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Gemini 2.5 Aktif</span>
          </div>

          {/* History Button */}
          <button
            onClick={onOpenHistory}
            className="relative flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium transition border border-slate-700 active:scale-95"
            title="Geçmiş Taramalar"
          >
            <History className="w-4 h-4 text-rose-400" />
            <span className="hidden sm:inline">Geçmiş</span>
            {historyCount > 0 && (
              <span className="bg-rose-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[18px] text-center">
                {historyCount}
              </span>
            )}
          </button>

          {/* New Scan Button */}
          <button
            onClick={onNewScan}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs sm:text-sm font-semibold shadow-md shadow-rose-900/30 transition active:scale-95"
          >
            <span>Yeni Tarama</span>
          </button>
        </div>
      </div>
    </header>
  );
};

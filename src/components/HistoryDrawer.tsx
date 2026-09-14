'use client';

import React, { useState } from 'react';
import { X, History, Trash2, Search, ArrowRight, ExternalLink } from 'lucide-react';
import { ProductAnalysis } from '@/lib/types';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  history: ProductAnalysis[];
  onSelectProduct: (analysis: ProductAnalysis) => void;
  onClearHistory: () => void;
  onDeleteScan: (id: string) => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  history,
  onSelectProduct,
  onClearHistory,
  onDeleteScan
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  const filteredHistory = history.filter((item) => {
    const q = searchTerm.toLowerCase();
    return (
      item.productName.toLowerCase().includes(q) ||
      item.brand.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/70 backdrop-blur-sm flex justify-end transition-opacity">
      <div
        className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Başlık */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-rose-400" />
            <h3 className="font-bold text-white text-base">
              Tarama Geçmişi ({history.length})
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Arama Alanı */}
        <div className="p-3 border-b border-slate-800/60">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Ürün veya marka ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 focus:border-rose-500 rounded-xl text-white text-xs outline-none transition"
            />
          </div>
        </div>

        {/* Liste */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredHistory.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <History className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-medium">Henüz kayıtlı tarama bulunamadı.</p>
              <p className="text-xs text-slate-600 mt-1">
                Fotoğraf yükleyip analiz ettiğiniz ürünler burada saklanır.
              </p>
            </div>
          ) : (
            filteredHistory.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelectProduct(item);
                  onClose();
                }}
                className="group p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-rose-500/40 cursor-pointer transition flex items-center gap-3 relative"
              >
                {item.imagePreview ? (
                  <img
                    src={item.imagePreview}
                    alt={item.productName}
                    className="w-14 h-14 rounded-lg object-contain bg-slate-900 border border-slate-800 shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 shrink-0">
                    <History className="w-6 h-6" />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[10px] font-bold text-rose-400 uppercase">
                      {item.brand}
                    </span>
                    <span className="text-slate-600 text-[10px]">•</span>
                    <span className="text-[10px] text-slate-400">
                      {new Date(item.createdAt).toLocaleDateString('tr-TR')}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-white truncate group-hover:text-rose-300 transition">
                    {item.productName}
                  </h4>

                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                        item.feasibility.score >= 70
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : item.feasibility.score >= 45
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-rose-500/20 text-rose-300'
                      }`}
                    >
                      {item.feasibility.score}/100 Puan
                    </span>

                    <span className="text-xs font-semibold text-slate-300">
                      {item.marketPrices.average.toLocaleString('tr-TR')} ₺
                    </span>
                  </div>
                </div>

                {/* Sil butonu */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteScan(item.id);
                  }}
                  className="p-1.5 text-slate-600 hover:text-rose-400 hover:bg-slate-900 rounded-lg transition"
                  title="Kaydı Sil"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Alt Bar: Tümünü Temizle */}
        {history.length > 0 && (
          <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
            <span className="text-xs text-slate-400">
              {history.length} ürün geçmişte kayıtlı
            </span>
            <button
              onClick={onClearHistory}
              className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 font-medium transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Tümünü Temizle</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

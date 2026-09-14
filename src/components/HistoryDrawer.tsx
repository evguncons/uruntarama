'use client';

import React, { useState } from 'react';
import { X, History, Trash2, Search, ArrowRight } from 'lucide-react';
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
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end transition-opacity">
      <div
        className="w-full max-w-md bg-white border-l border-pink-100 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Başlık */}
        <div className="p-4 border-b border-pink-100 flex items-center justify-between bg-pink-50/30">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-fuchsia-600" />
            <h3 className="font-black text-slate-900 text-base">
              Tarama Geçmişi ({history.length})
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Arama Alanı */}
        <div className="p-3 border-b border-pink-100">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Ürün veya marka ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-200 focus:border-fuchsia-500 focus:bg-white rounded-xl text-slate-900 text-xs font-semibold outline-none transition"
            />
          </div>
        </div>

        {/* Liste */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredHistory.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <History className="w-10 h-10 mx-auto mb-2 opacity-30 text-fuchsia-400" />
              <p className="text-sm font-bold text-slate-600">Henüz kayıtlı tarama bulunamadı.</p>
              <p className="text-xs text-slate-400 mt-1">
                Fotoğraf çekip analiz ettiğiniz ürünler burada saklanır.
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
                className="group p-3.5 rounded-2xl bg-slate-50/70 border border-slate-200/80 hover:border-fuchsia-400 hover:bg-white cursor-pointer transition flex items-center gap-3 relative shadow-2xs"
              >
                {item.imagePreview ? (
                  <img
                    src={item.imagePreview}
                    alt={item.productName}
                    className="w-14 h-14 rounded-xl object-contain bg-white border border-slate-200 shrink-0 p-1"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-slate-400 shrink-0">
                    <History className="w-6 h-6 text-fuchsia-500" />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[10px] font-black text-fuchsia-700 uppercase">
                      {item.brand}
                    </span>
                    <span className="text-slate-300 text-[10px]">•</span>
                    <span className="text-[10px] text-slate-400 font-medium">
                      {new Date(item.createdAt).toLocaleDateString('tr-TR')}
                    </span>
                  </div>

                  <h4 className="text-xs font-black text-slate-800 truncate group-hover:text-fuchsia-700 transition">
                    {item.productName}
                  </h4>

                  <div className="flex items-center gap-2 mt-1.5">
                    <span
                      className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                        item.feasibility.score >= 70
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.feasibility.score >= 45
                          ? 'bg-fuchsia-100 text-fuchsia-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {item.feasibility.score}/100 Puan
                    </span>

                    <span className="text-xs font-bold text-slate-700">
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
                  className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition"
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
          <div className="p-4 border-t border-pink-100 bg-pink-50/30 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">
              {history.length} ürün kayıtlı
            </span>
            <button
              onClick={onClearHistory}
              className="text-xs text-rose-600 hover:text-rose-700 flex items-center gap-1 font-bold transition"
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

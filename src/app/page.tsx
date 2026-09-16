'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { ImageUploader } from '@/components/ImageUploader';
import { AnalysisResult } from '@/components/AnalysisResult';
import { HistoryDrawer } from '@/components/HistoryDrawer';
import { ProductAnalysis } from '@/lib/types';
import {
  Sparkles,
  TrendingUp,
  ShieldCheck,
  ShoppingBag,
  CreditCard,
  Target,
  ArrowRight,
  AlertCircle
} from 'lucide-react';

const STORAGE_KEY = 'HEDEF_AVM_SCAN_HISTORY_V1';

export default function Home() {
  const [analysis, setAnalysis] = useState<ProductAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<ProductAnalysis[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      const parsed: unknown = saved ? JSON.parse(saved) : [];
      return Array.isArray(parsed) ? parsed as ProductAnalysis[] : [];
    } catch {
      return [];
    }
  });
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);

  // Geçmişi kaydet
  const saveToHistory = (newAnalysis: ProductAnalysis) => {
    try {
      const updated = [newAnalysis, ...history.filter((h) => h.id !== newAnalysis.id)].slice(0, 30);
      setHistory(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (err) {
      console.warn('Geçmiş kaydedilemedi:', err);
    }
  };

  // Yeni ürün analizi isteği
  const handleAnalyze = async (params: {
    productName: string;
    base64: string;
    mimeType: string;
    userCost?: number;
    notes?: string;
  }) => {
    try {
      setIsLoading(true);
      setErrorMessage(null);

      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          productName: params.productName,
          imageBase64: params.base64,
          mimeType: params.mimeType,
          userCost: params.userCost,
          additionalNotes: params.notes
        })
      });

      const resJson = await response.json();

      if (!response.ok) {
        throw new Error(resJson.error || 'Analiz işlemi gerçekleştirilemedi.');
      }

      if (!resJson.data) {
        throw new Error('Geçersiz analiz yanıtı alındı.');
      }

      const completedAnalysis: ProductAnalysis = {
        ...resJson.data,
        imagePreview: params.base64
      };

      setAnalysis(completedAnalysis);
      saveToHistory(completedAnalysis);

      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: unknown) {
      console.error('Analiz Hatası:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Ürün analizi sırasında bir hata oluştu.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewScan = () => {
    setAnalysis(null);
    setErrorMessage(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectProduct = (item: ProductAnalysis) => {
    setAnalysis(item);
    setErrorMessage(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleClearHistory = () => {
    if (confirm('Tüm tarama geçmişinizi silmek istediğinize emin misiniz?')) {
      setHistory([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleDeleteScan = (id: string) => {
    const updated = history.filter((item) => item.id !== id);
    setHistory(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    if (analysis?.id === id) {
      setAnalysis(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#faf5f8] text-slate-900 selection:bg-fuchsia-600 selection:text-white relative">
      {/* Arka Plan Işık Efektleri (Açık Magenta Tonlar) */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-fuchsia-300/20 blur-[130px] rounded-full"></div>
        <div className="absolute top-1/3 -left-40 w-[450px] h-[450px] bg-pink-300/20 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-10 right-0 w-[500px] h-[500px] bg-rose-200/20 blur-[140px] rounded-full"></div>
      </div>

      {/* Üst Başlık (Navbar) */}
      <Header
        onOpenHistory={() => setIsHistoryOpen(true)}
        historyCount={history.length}
        onNewScan={handleNewScan}
      />

      {/* Ana İçerik */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 z-10">
        {/* Hata Bildirimi */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3 shadow-md">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <strong className="font-bold block mb-0.5">İşlem Başarısız:</strong>
              <p>{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-700 hover:text-rose-900 text-xs font-bold px-2.5 py-1 rounded-lg bg-rose-100 border border-rose-200"
            >
              Kapat
            </button>
          </div>
        )}

        {/* Analiz Sonucu Varsa Onu Göster, Yoksa Yükleyiciyi Göster */}
        {analysis ? (
          <AnalysisResult analysis={analysis} onNewScan={handleNewScan} />
        ) : (
          <div className="space-y-8">
            {/* Hero / Bilgi Şeridi */}
            <div className="text-center max-w-3xl mx-auto space-y-4 pt-2 pb-2">
              <div className="flex justify-center mb-1">
                <img
                  src="/hedef-logo.png"
                  alt="Hedef Alışveriş Merkezleri - Evinizin Rengi"
                  className="h-16 sm:h-20 w-auto object-contain drop-shadow-sm hover:scale-105 transition-transform"
                />
              </div>

              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-pink-50 border border-pink-200 text-[#c81373] text-xs font-black shadow-2xs">
                <Target className="w-4 h-4 text-[#c81373]" />
                <span>Hedef AVM Satın Alma ve Perakende İstihbarat Radarı</span>
              </div>

              <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 tracking-tight">
                Ürün Satış Potansiyelini{' '}
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#c81373] via-rose-600 to-pink-600">
                  Yapay Zeka ile Ölçün
                </span>
              </h1>

              <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-2xl mx-auto font-medium">
                Yeni bir ürün mü gördünüz? Fotoğrafını çekin veya yükleyin; yapay zeka Türkiye pazarındaki
                fiyatları incelesin, <strong>Hedef AVM&apos;ye özel elden senetli ve peşin</strong> satış stratejisini kurgulasın,
                satılabilirlik puanı ve vitrin sloganı önersin.
              </p>
            </div>

            {/* Kamera & Görsel Yükleyici */}
            <ImageUploader onAnalyze={handleAnalyze} isLoading={isLoading} />

            {/* Kurumsal Yetenek Rozetleri */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
              <div className="bg-white border border-pink-100 rounded-3xl p-5 shadow-lg shadow-fuchsia-950/5 flex items-start gap-3.5">
                <div className="p-3 rounded-2xl bg-fuchsia-50 text-fuchsia-600 border border-fuchsia-200 shrink-0">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-black text-slate-900 mb-1">
                    Güncel Piyasa Fiyatları
                  </h4>
                  <p className="text-xs text-slate-500 leading-relaxed font-medium">
                    Trendyol, Hepsiburada ve perakende mağazalarının anlık fiyat skalası ve rekabeti.
                  </p>
                </div>
              </div>

              <div className="bg-white border border-pink-100 rounded-3xl p-5 shadow-lg shadow-fuchsia-950/5 flex items-start gap-3.5">
                <div className="p-3 rounded-2xl bg-pink-50 text-pink-600 border border-pink-200 shrink-0">
                  <CreditCard className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-black text-slate-900 mb-1">
                    Elden Senetli Satış Modeli
                  </h4>
                  <p className="text-xs text-slate-500 leading-relaxed font-medium">
                    Hedef AVM müşterilerine özel 12-15 ay vadeli elden senetli taksit ve kâr hesabı.
                  </p>
                </div>
              </div>

              <div className="bg-white border border-pink-100 rounded-3xl p-5 shadow-lg shadow-fuchsia-950/5 flex items-start gap-3.5">
                <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-black text-slate-900 mb-1">
                    &quot;Satar mı?&quot; Fizibilitesi
                  </h4>
                  <p className="text-xs text-slate-500 leading-relaxed font-medium">
                    0-100 Puan, pazar talebi, iade riski ve mağaza içi kampanya kurguları.
                  </p>
                </div>
              </div>
            </div>

            {/* Son Taramalar Önizlemesi (Varsa) */}
            {history.length > 0 && (
              <div className="pt-6 border-t border-pink-100">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-fuchsia-600" />
                    <h3 className="text-sm font-black text-slate-900">
                      Son Taranan Ürünler
                    </h3>
                  </div>
                  <button
                    onClick={() => setIsHistoryOpen(true)}
                    className="text-xs text-fuchsia-700 hover:text-fuchsia-800 font-bold flex items-center gap-1"
                  >
                    <span>Tümünü Gör ({history.length})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                  {history.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleSelectProduct(item)}
                      className="group p-3.5 rounded-2xl bg-white border border-pink-100 hover:border-fuchsia-400 hover:shadow-md cursor-pointer transition flex items-center gap-3.5 shadow-xs"
                    >
                      {item.imagePreview ? (
                        <img
                          src={item.imagePreview}
                          alt={item.productName}
                          className="w-13 h-13 rounded-xl object-contain bg-slate-50 border border-slate-100 shrink-0 p-1"
                        />
                      ) : (
                        <div className="w-13 h-13 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center text-fuchsia-600 shrink-0">
                          <ShoppingBag className="w-5 h-5" />
                        </div>
                      )}

                      <div className="flex-1 min-w-0">
                        <span className="text-[10px] font-black text-fuchsia-700 uppercase block truncate">
                          {item.brand}
                        </span>
                        <h4 className="text-xs font-black text-slate-900 truncate group-hover:text-fuchsia-700 transition">
                          {item.productName}
                        </h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] font-black px-2 py-0.5 rounded-md bg-fuchsia-50 text-fuchsia-800 border border-fuchsia-200">
                            {item.feasibility.score} Puan
                          </span>
                          <span className="text-xs font-black text-slate-700">
                            {item.marketPrices.average.toLocaleString('tr-TR')} ₺
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Geçmiş Yan Çekmecesi */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onSelectProduct={handleSelectProduct}
        onClearHistory={handleClearHistory}
        onDeleteScan={handleDeleteScan}
      />

      {/* Alt Bilgi (Footer) */}
      <footer className="w-full border-t border-pink-100 bg-white/90 backdrop-blur py-6 text-center text-xs text-slate-500 mt-12">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <img
              src="/hedef-logo.png"
              alt="Hedef Alışveriş Merkezleri"
              className="h-8 w-auto object-contain"
            />
            <span className="text-slate-300">|</span>
            <span className="font-bold text-slate-600">Özel Ürün Piyasa Araştırması AI Yazılımı</span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">
            Google Gemini 2.5 Vision & Perakende İstihbarat Motoru ile güçlendirilmiştir.
          </p>
        </div>
      </footer>
    </div>
  );
}

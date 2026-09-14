'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { ImageUploader } from '@/components/ImageUploader';
import { AnalysisResult } from '@/components/AnalysisResult';
import { HistoryDrawer } from '@/components/HistoryDrawer';
import { ProductAnalysis } from '@/lib/types';
import {
  Sparkles,
  TrendingUp,
  ShieldCheck,
  Zap,
  ShoppingBag,
  CreditCard,
  Target,
  ArrowRight,
  HelpCircle,
  AlertCircle
} from 'lucide-react';

const STORAGE_KEY = 'HEDEF_AVM_SCAN_HISTORY_V1';

export default function Home() {
  const [analysis, setAnalysis] = useState<ProductAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<ProductAnalysis[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);

  // Tarama geçmişini yerel depolamadan yükle
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setHistory(parsed);
        }
      }
    } catch (err) {
      console.warn('Geçmiş yüklenemedi:', err);
    }
  }, []);

  // Geçmişi kaydet
  const saveToHistory = (newAnalysis: ProductAnalysis) => {
    try {
      // LocalStorage kota sınırını aşmamak için resim verisini thumbnail olarak sınırlayabiliriz
      const updated = [newAnalysis, ...history.filter((h) => h.id !== newAnalysis.id)].slice(0, 30);
      setHistory(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (err) {
      console.warn('Geçmiş kaydedilemedi (kotaya takılmış olabilir):', err);
    }
  };

  // Yeni ürün analizi isteği
  const handleAnalyze = async (params: {
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

      // Sayfayı yumuşakça sonuca kaydır
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      console.error('Analiz Hatası:', err);
      setErrorMessage(err.message || 'Ürün analizi sırasında bir hata oluştu.');
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
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-rose-600 selection:text-white relative">
      {/* Arka Plan Işık Efektleri */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-rose-600/10 blur-[130px] rounded-full"></div>
        <div className="absolute top-1/3 -left-40 w-[450px] h-[450px] bg-blue-600/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-10 right-0 w-[500px] h-[500px] bg-amber-600/5 blur-[140px] rounded-full"></div>
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
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/15 border border-rose-500/40 text-rose-300 text-sm flex items-start gap-3 shadow-lg">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <strong className="font-bold block mb-0.5">İşlem Başarısız:</strong>
              <p>{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-white text-xs font-semibold px-2 py-1 rounded bg-rose-950/40 border border-rose-500/30"
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
            <div className="text-center max-w-3xl mx-auto space-y-3 pt-2 pb-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-950/60 border border-rose-500/30 text-rose-300 text-xs font-semibold shadow-inner">
                <Target className="w-3.5 h-3.5 text-rose-400" />
                <span>Hedef AVM Satın Alma ve Mağaza Satış Radarı</span>
              </div>

              <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight">
                Ürün Satış Potansiyelini{' '}
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-rose-400 via-red-300 to-amber-300">
                  Yapay Zeka ile Ölçün
                </span>
              </h1>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl mx-auto">
                Yeni bir ürün mü keşfettiniz? Fotoğrafını çekin; yapay zeka Türkiye pazarındaki
                fiyatları incelesin, <strong>elden senetli ve peşin</strong> satış stratejisini kursun,
                ürüne satılabilirlik puanı verip kampanya sloganı önersin.
              </p>
            </div>

            {/* Kamera & Görsel Yükleyici */}
            <ImageUploader onAnalyze={handleAnalyze} isLoading={isLoading} />

            {/* Kurumsal Yetenek Rozetleri */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 shrink-0">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white mb-1">
                    Güncel Piyasa Fiyatları
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Trendyol, Hepsiburada ve perakende mağazalarının anlık fiyat skalası.
                  </p>
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
                  <CreditCard className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white mb-1">
                    Elden Senetli Satış Modeli
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Hedef AVM müşterilerine özel 12-15 ay vadeli elden taksit ve kâr hesabı.
                  </p>
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white mb-1">
                    "Satar mı?" Fizibilitesi
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    0-100 Puan, talep seviyesi, riskler ve mağaza içi kampanya kurguları.
                  </p>
                </div>
              </div>
            </div>

            {/* Son Taramalar Önizlemesi (Varsa) */}
            {history.length > 0 && (
              <div className="pt-6 border-t border-slate-800/80">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-rose-400" />
                    <h3 className="text-sm font-bold text-white">
                      Son Taranan Ürünler
                    </h3>
                  </div>
                  <button
                    onClick={() => setIsHistoryOpen(true)}
                    className="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1"
                  >
                    <span>Tümünü Gör ({history.length})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {history.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleSelectProduct(item)}
                      className="group p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-rose-500/50 cursor-pointer transition flex items-center gap-3"
                    >
                      {item.imagePreview ? (
                        <img
                          src={item.imagePreview}
                          alt={item.productName}
                          className="w-12 h-12 rounded-lg object-contain bg-slate-950 border border-slate-800 shrink-0"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-500 shrink-0">
                          <ShoppingBag className="w-5 h-5" />
                        </div>
                      )}

                      <div className="flex-1 min-w-0">
                        <span className="text-[10px] font-bold text-rose-400 uppercase block truncate">
                          {item.brand}
                        </span>
                        <h4 className="text-xs font-bold text-white truncate group-hover:text-rose-300 transition">
                          {item.productName}
                        </h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                            {item.feasibility.score} Puan
                          </span>
                          <span className="text-xs font-semibold text-emerald-400">
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
      <footer className="w-full border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500 mt-12">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-300">HEDEF AVM</span>
            <span>•</span>
            <span>Özel Ürün Piyasa Araştırması AI Yazılımı</span>
          </div>
          <p className="text-[11px] text-slate-500">
            Google Gemini 2.5 Vision & Search Intelligence motoru ile güçlendirilmiştir.
          </p>
        </div>
      </footer>
    </div>
  );
}

'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Camera,
  UploadCloud,
  Image as ImageIcon,
  RotateCcw,
  Sparkles,
  DollarSign,
  FileText,
  Video,
  X,
  RefreshCw,
  Zap
} from 'lucide-react';
import { optimizeImageFile } from '@/lib/imageUtils';

interface ImageUploaderProps {
  onAnalyze: (data: {
    base64: string;
    mimeType: string;
    userCost?: number;
    notes?: string;
  }) => void;
  isLoading: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onAnalyze,
  isLoading
}) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [base64Data, setBase64Data] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState<string>('image/jpeg');
  const [userCost, setUserCost] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Canlı kamera vizörü durumu
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraFacing, setCameraFacing] = useState<'environment' | 'user'>('environment');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Dosya input referansları
  const galleryInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  // Analiz adımları animasyon metni
  const [loadingStep, setLoadingStep] = useState<number>(0);
  const loadingMessages = [
    'Ürün görseli ve ambalaj detayları taranıyor...',
    'Trendyol, Hepsiburada ve Amazon pazar fiyatları araştırılıyor...',
    'Hedef AVM elden senetli taksit kurgusu hesaplanıyor...',
    'Piyasa satılabilirlik puanı ve kampanya önerileri derleniyor...'
  ];

  useEffect(() => {
    let interval: any;
    if (isLoading) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev + 1) % loadingMessages.length);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  // Canlı kamera akışını başlat
  const startLiveCamera = async () => {
    try {
      setErrorMessage(null);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: cameraFacing },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (err) {
      console.warn('Live camera getUserMedia error, falling back to native file capture:', err);
      // Kamera izni verilmediyse veya desteklenmiyorsa standart inputu tetikle
      if (cameraInputRef.current) {
        cameraInputRef.current.click();
      }
    }
  };

  // Kamerayı kapat
  const stopLiveCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  // Kamerayı ön/arka arasında değiştir
  const switchCameraFacing = () => {
    const nextFacing = cameraFacing === 'environment' ? 'user' : 'environment';
    setCameraFacing(nextFacing);
    setTimeout(() => {
      startLiveCamera();
    }, 100);
  };

  // Canlı video akışından anlık görüntü yakala
  const capturePhotoFromLiveStream = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.88);

    setPreview(dataUrl);
    setBase64Data(dataUrl);
    setMimeType('image/jpeg');
    stopLiveCamera();
  };

  // Dosya işleme (Galeri veya Native Kamera)
  const processFile = async (file: File) => {
    try {
      setErrorMessage(null);
      if (!file.type.startsWith('image/')) {
        setErrorMessage('Lütfen geçerli bir resim dosyası seçiniz (JPG, PNG, WEBP).');
        return;
      }

      const optimized = await optimizeImageFile(file);
      setPreview(optimized.previewUrl);
      setBase64Data(optimized.base64);
      setMimeType(optimized.mimeType);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Görsel işlenirken bir sorun oluştu.');
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  // Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  // Analizi Gönder
  const handleStartAnalysis = () => {
    if (!base64Data) {
      setErrorMessage('Lütfen önce bir ürün fotoğrafı çekin veya yükleyin.');
      return;
    }

    const costNum = userCost.trim() !== '' ? Number(userCost) : undefined;
    onAnalyze({
      base64: base64Data,
      mimeType: mimeType,
      userCost: costNum,
      notes: notes.trim() !== '' ? notes.trim() : undefined
    });
  };

  const handleClearImage = () => {
    setPreview(null);
    setBase64Data(null);
    stopLiveCamera();
  };

  return (
    <div className="w-full bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-3xl p-4 sm:p-7 shadow-2xl relative overflow-hidden">
      {/* Gizli Dosya Girişleri */}
      <input
        ref={galleryInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInputChange}
        className="hidden"
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Başlık ve Açıklama */}
      <div className="text-center max-w-2xl mx-auto mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold mb-2">
          <Zap className="w-3.5 h-3.5" />
          <span>Yapay Zeka Destekli Anlık Piyasa İstihbaratı</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
          Ürün Fotoğrafını Yükleyin veya Kamerayla Çekin
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Ürünün kutusunu, etiketini veya kendisini çekin; Gemini AI piyasa fiyatlarını, rekabeti ve Hedef AVM taksitli satış potansiyelini anında çıkarsın.
        </p>
      </div>

      {/* Canlı Kamera Modu Açıkken */}
      {isCameraActive ? (
        <div className="relative rounded-2xl overflow-hidden bg-black aspect-video max-h-[480px] w-full flex items-center justify-center border-2 border-rose-500/50 shadow-2xl">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />

          {/* Kamera Vizör Kılavuz Çizgileri */}
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center p-8">
            <div className="w-full max-w-md h-4/5 border-2 border-dashed border-rose-400/60 rounded-2xl relative">
              <div className="absolute top-2 left-3 bg-slate-900/80 backdrop-blur px-2.5 py-1 rounded text-[11px] text-white font-medium">
                Ürünü veya barkodu bu alana hizalayın
              </div>
            </div>
          </div>

          {/* Kamera Kontrolleri */}
          <div className="absolute bottom-4 inset-x-0 flex items-center justify-center gap-4 px-4">
            <button
              onClick={switchCameraFacing}
              type="button"
              className="p-3 rounded-full bg-slate-800/80 text-white backdrop-blur hover:bg-slate-700 transition"
              title="Kamerayı Değiştir"
            >
              <RefreshCw className="w-5 h-5" />
            </button>

            <button
              onClick={capturePhotoFromLiveStream}
              type="button"
              className="w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-500 border-4 border-white flex items-center justify-center shadow-lg transition active:scale-90"
              title="Fotoğraf Çek"
            >
              <Camera className="w-8 h-8 text-white" />
            </button>

            <button
              onClick={stopLiveCamera}
              type="button"
              className="p-3 rounded-full bg-slate-800/80 text-white backdrop-blur hover:bg-slate-700 transition"
              title="Kamerayı Kapat"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      ) : preview ? (
        /* Seçilen Görselin Önizlemesi */
        <div className="relative rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 max-h-[420px] w-full flex items-center justify-center">
          <img
            src={preview}
            alt="Yüklenen Ürün"
            className="w-full h-full max-h-[400px] object-contain"
          />

          <div className="absolute top-3 right-3 flex items-center gap-2">
            <button
              onClick={handleClearImage}
              className="p-2 rounded-xl bg-slate-900/80 backdrop-blur text-rose-400 hover:bg-rose-600 hover:text-white transition shadow-lg border border-slate-700"
              title="Görseli Değiştir"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur px-3 py-1.5 rounded-xl border border-slate-800 text-xs text-emerald-400 font-semibold flex items-center gap-1.5 shadow-md">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Görsel Hazır</span>
          </div>
        </div>
      ) : (
        /* Yükleme & Kamera Seçim Alanı */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-6 sm:p-10 transition text-center flex flex-col items-center justify-center cursor-pointer ${
            isDragging
              ? 'border-rose-500 bg-rose-500/10'
              : 'border-slate-700 hover:border-rose-500/50 bg-slate-950/50 hover:bg-slate-950/80'
          }`}
          onClick={() => galleryInputRef.current?.click()}
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600/20 to-amber-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-4 shadow-inner">
            <UploadCloud className="w-8 h-8" />
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 mb-3">
            {/* Canlı Kamera Butonu */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                startLiveCamera();
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs sm:text-sm shadow-md shadow-rose-900/40 transition active:scale-95"
            >
              <Camera className="w-4 h-4" />
              <span>Fotoğraf Çek (Kamera)</span>
            </button>

            {/* Galeri Seçim Butonu */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                galleryInputRef.current?.click();
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs sm:text-sm border border-slate-700 transition active:scale-95"
            >
              <ImageIcon className="w-4 h-4 text-rose-400" />
              <span>Galeriden Seç</span>
            </button>
          </div>

          <p className="text-xs text-slate-400">
            veya fotoğrafı buraya sürükleyip bırakın (JPG, PNG, WEBP, Maks. 10MB)
          </p>
        </div>
      )}

      {/* Hata Bildirimi */}
      {errorMessage && (
        <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium text-center">
          {errorMessage}
        </div>
      )}

      {/* Ek Bilgiler: Alış Fiyatı & Not */}
      <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 border-t border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-rose-400" />
            <span>Tedarikçi Alış Fiyatı (Opsiyonel)</span>
          </label>
          <div className="relative">
            <input
              type="number"
              min="0"
              placeholder="Örn: 2450 (Kârlılık hesabı için)"
              value={userCost}
              onChange={(e) => setUserCost(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 focus:border-rose-500 rounded-xl px-3 py-2 text-white text-xs sm:text-sm outline-none transition"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs font-bold">
              ₺
            </span>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-rose-400" />
            <span>Ekstra Not / Model Kodu (Opsiyonel)</span>
          </label>
          <input
            type="text"
            placeholder="Örn: Sıfır kutulu, 2 yıl garantili, 3 parça set"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 focus:border-rose-500 rounded-xl px-3 py-2 text-white text-xs sm:text-sm outline-none transition"
          />
        </div>
      </div>

      {/* Aksiyon Butonu */}
      <div className="mt-6 flex flex-col items-center">
        <button
          onClick={handleStartAnalysis}
          disabled={!preview || isLoading}
          className={`w-full sm:w-auto min-w-[260px] flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-2xl font-bold text-sm sm:text-base text-white shadow-xl transition-all ${
            !preview || isLoading
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-60'
              : 'bg-gradient-to-r from-rose-600 via-red-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 active:scale-95 shadow-rose-900/50'
          }`}
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin text-white" />
              <span>Yapay Zeka Analiz Ediyor...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-amber-300" />
              <span>Piyasa Analizini Başlat</span>
            </>
          )}
        </button>

        {/* Dinamik Yükleniyor Adımları */}
        {isLoading && (
          <div className="mt-4 flex items-center gap-2 text-xs text-rose-300 animate-pulse font-medium">
            <span className="w-2 h-2 rounded-full bg-rose-400"></span>
            <span>{loadingMessages[loadingStep]}</span>
          </div>
        )}
      </div>
    </div>
  );
};

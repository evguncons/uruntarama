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
  X,
  RefreshCw,
  Zap,
  Tag,
  AlertCircle
} from 'lucide-react';
import { optimizeImageFile } from '@/lib/imageUtils';

interface ImageUploaderProps {
  onAnalyze: (data: {
    productName: string;
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
  const [productName, setProductName] = useState<string>('');
  const [preview, setPreview] = useState<string | null>(null);
  const [base64Data, setBase64Data] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState<string>('image/jpeg');
  const [userCost, setUserCost] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const productNameInputRef = useRef<HTMLInputElement | null>(null);

  // Canlı kamera vizörü durumu
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraFacing, setCameraFacing] = useState<'environment' | 'user'>('environment');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Dosya input referansları
  const galleryInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  // Analiz adımları animasyon metni (2 Aşamalı Canlı Piyasa Taraması)
  const [loadingStep, setLoadingStep] = useState<number>(0);
  const loadingMessages = [
    '1. Aşama: Google üzerinden Akakçe, Trendyol ve Hepsiburada fiyatları canlı taranıyor...',
    '2. Aşama: Yüklenen görseldeki ürün detayları ve ambalajı inceleniyor...',
    '3. Aşama: Hedef AVM 12 ay elden senetli taksit planı hesaplanıyor...',
    '4. Aşama: Satılabilirlik puanı ve vitrin afiş sloganları oluşturuluyor...'
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

  // Analizi Gönder (Zorunlu Ürün Adı Kontrolü)
  const handleStartAnalysis = () => {
    const trimmedName = productName.trim();
    if (!trimmedName || trimmedName.length < 2) {
      setErrorMessage(
        '⚠️ Model karışıklığını önlemek ve Trendyol/Hepsiburada fiyatlarını hatasız çekebilmek için lütfen ÜRÜN ADI VE MODELİNİ giriniz (Örn: iPhone 15 128GB, Philips HD9650 Airfryer vb.).'
      );
      productNameInputRef.current?.focus();
      return;
    }

    if (!base64Data) {
      setErrorMessage('Lütfen önce analiz edilecek ürün fotoğrafını çekin veya galeriden seçin.');
      return;
    }

    const costNum = userCost.trim() !== '' ? Number(userCost) : undefined;
    onAnalyze({
      productName: trimmedName,
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
    <div className="w-full bg-white border border-pink-100 rounded-3xl p-5 sm:p-8 shadow-xl shadow-fuchsia-950/5 relative overflow-hidden transition-all">
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
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-pink-50 border border-pink-200 text-[#c81373] text-xs font-black mb-2 shadow-2xs">
          <Zap className="w-3.5 h-3.5 text-[#c81373]" />
          <span>Canlı Google & Pazaryeri Taramalı Yapay Zeka Radarı</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          Ürün Bilgisini ve Fotoğrafını Ekleyin
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 font-medium mt-1 leading-relaxed">
          Model karışıklığını önlemek ve Trendyol, Hepsiburada ve Akakçe fiyatlarını <strong>canlı ve doğru</strong> çekebilmek için lütfen ürün adını ve modelini belirtin.
        </p>
      </div>

      {/* ZORUNLU ÜRÜN ADI / MODELİ GİRİŞİ */}
      <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-pink-50/70 via-fuchsia-50/40 to-white border-2 border-[#c81373]/30 shadow-sm">
        <label className="block text-xs sm:text-sm font-black text-slate-900 mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Tag className="w-4 h-4 text-[#c81373]" />
            <span>Ürün Adı ve Modeli</span>
            <span className="text-rose-600 font-black text-base">* (Zorunlu)</span>
          </span>
          <span className="text-[11px] text-[#c81373] font-bold bg-pink-100/80 px-2 py-0.5 rounded-md">
            Doğru Model & Canlı Fiyat İçin Şart
          </span>
        </label>
        <div className="relative">
          <input
            ref={productNameInputRef}
            type="text"
            required
            placeholder="Örn: iPhone 15 128GB, Philips HD9650 Airfryer, Karaca Hatır Hüps..."
            value={productName}
            onChange={(e) => {
              setProductName(e.target.value);
              if (errorMessage) setErrorMessage(null);
            }}
            className="w-full pl-4 pr-10 py-3 bg-white border-2 border-pink-200 focus:border-[#c81373] focus:ring-4 focus:ring-[#c81373]/15 rounded-xl text-slate-900 font-bold text-sm sm:text-base outline-none transition placeholder:text-slate-400 shadow-2xs"
          />
          {productName.trim().length > 0 && (
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-emerald-600 text-xs font-black bg-emerald-50 px-2 py-0.5 rounded">
              ✓ Hazır
            </span>
          )}
        </div>
        <p className="text-[11px] text-slate-500 mt-1.5 font-medium">
          💡 <strong>İpucu:</strong> Telefon veya elektroniklerde kapasite (128GB/256GB), model numarası ve rengi yazmak Akakçe/Trendyol fiyatlarını %100 doğrular.
        </p>
      </div>

      {/* Canlı Kamera Modu Açıkken */}
      {isCameraActive ? (
        <div className="relative rounded-3xl overflow-hidden bg-black aspect-video max-h-[480px] w-full flex items-center justify-center border-2 border-[#c81373] shadow-2xl mb-6">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />

          {/* Kamera Vizör Kılavuz Çizgileri */}
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center p-8">
            <div className="w-full max-w-md h-4/5 border-2 border-dashed border-[#c81373]/80 rounded-2xl relative">
              <div className="absolute top-2 left-3 bg-white/90 backdrop-blur px-2.5 py-1 rounded-md text-[11px] text-[#c81373] font-bold shadow-sm">
                Ürünü veya barkodu bu alana hizalayın
              </div>
            </div>
          </div>

          {/* Kamera Kontrolleri */}
          <div className="absolute bottom-4 inset-x-0 flex items-center justify-center gap-4 px-4">
            <button
              onClick={switchCameraFacing}
              type="button"
              className="p-3.5 rounded-full bg-white/90 text-slate-800 backdrop-blur hover:bg-white shadow-lg transition"
              title="Kamerayı Değiştir"
            >
              <RefreshCw className="w-5 h-5 text-[#c81373]" />
            </button>

            <button
              onClick={capturePhotoFromLiveStream}
              type="button"
              className="w-16 h-16 rounded-full bg-gradient-to-tr from-[#c81373] to-pink-500 hover:from-[#b01065] hover:to-pink-400 border-4 border-white flex items-center justify-center shadow-xl transition active:scale-90"
              title="Fotoğraf Çek"
            >
              <Camera className="w-8 h-8 text-white" />
            </button>

            <button
              onClick={stopLiveCamera}
              type="button"
              className="p-3.5 rounded-full bg-white/90 text-slate-800 backdrop-blur hover:bg-white shadow-lg transition"
              title="Kamerayı Kapat"
            >
              <X className="w-5 h-5 text-rose-600" />
            </button>
          </div>
        </div>
      ) : preview ? (
        /* Seçilen Görselin Önizlemesi */
        <div className="relative rounded-3xl overflow-hidden bg-slate-50 border border-pink-100 max-h-[400px] w-full flex items-center justify-center p-4 mb-6">
          <img
            src={preview}
            alt="Yüklenen Ürün"
            className="w-full h-full max-h-[360px] object-contain rounded-2xl"
          />

          <div className="absolute top-4 right-4 flex items-center gap-2">
            <button
              onClick={handleClearImage}
              className="p-2.5 rounded-2xl bg-white/90 backdrop-blur text-rose-600 hover:bg-rose-500 hover:text-white transition shadow-md border border-pink-100"
              title="Görseli Değiştir"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur px-3 py-1.5 rounded-xl border border-pink-200 text-xs text-[#c81373] font-bold flex items-center gap-1.5 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#c81373]" />
            <span>Fotoğraf Hazır</span>
          </div>
        </div>
      ) : (
        /* Yükleme & Kamera Seçim Alanı */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-3xl p-7 sm:p-10 transition text-center flex flex-col items-center justify-center cursor-pointer mb-6 ${
            isDragging
              ? 'border-[#c81373] bg-pink-50/60'
              : 'border-pink-200/90 hover:border-[#c81373] bg-gradient-to-b from-pink-50/30 via-white to-fuchsia-50/20 hover:bg-pink-50/40'
          }`}
          onClick={() => galleryInputRef.current?.click()}
        >
          <div className="w-16 h-16 rounded-3xl bg-pink-50 border border-pink-200 flex items-center justify-center text-[#c81373] mb-3.5 shadow-xs">
            <UploadCloud className="w-8 h-8" />
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 mb-2.5">
            {/* Canlı Kamera Butonu */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                startLiveCamera();
              }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#c81373] to-rose-600 hover:from-[#b01065] hover:to-rose-500 text-white font-bold text-xs sm:text-sm shadow-md shadow-[#c81373]/25 transition active:scale-95"
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
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-bold text-xs sm:text-sm border border-slate-200 shadow-xs transition active:scale-95"
            >
              <ImageIcon className="w-4 h-4 text-[#c81373]" />
              <span>Galeriden Seç</span>
            </button>
          </div>

          <p className="text-xs text-slate-400 font-medium">
            veya fotoğrafı bu alana sürükleyip bırakın (JPG, PNG, WEBP)
          </p>
        </div>
      )}

      {/* Hata Bildirimi */}
      {errorMessage && (
        <div className="mb-5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs sm:text-sm font-bold flex items-start gap-2.5 shadow-xs">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">{errorMessage}</div>
        </div>
      )}

      {/* Ek Bilgiler: Alış Fiyatı & Not */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-5 border-t border-pink-100">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-[#c81373]" />
            <span>Tedarikçi Alış Fiyatı (Opsiyonel)</span>
          </label>
          <div className="relative">
            <input
              type="number"
              min="0"
              placeholder="Örn: 2450 (Kârlılık simülasyonu için)"
              value={userCost}
              onChange={(e) => setUserCost(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 focus:border-[#c81373] focus:bg-white focus:ring-2 focus:ring-[#c81373]/20 rounded-2xl px-3.5 py-2.5 text-slate-900 font-semibold text-xs sm:text-sm outline-none transition"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#c81373] text-xs font-black">
              ₺
            </span>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-[#c81373]" />
            <span>Ekstra Not / Renk / Durum (Opsiyonel)</span>
          </label>
          <input
            type="text"
            placeholder="Örn: Sıfır kutulu, Yıldız Işığı rengi, 2 yıl Türkiye garantili"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 focus:border-[#c81373] focus:bg-white focus:ring-2 focus:ring-[#c81373]/20 rounded-2xl px-3.5 py-2.5 text-slate-900 font-semibold text-xs sm:text-sm outline-none transition"
          />
        </div>
      </div>

      {/* Aksiyon Butonu */}
      <div className="mt-7 flex flex-col items-center">
        <button
          onClick={handleStartAnalysis}
          disabled={isLoading}
          className={`w-full sm:w-auto min-w-[300px] flex items-center justify-center gap-2.5 px-8 py-4 rounded-2xl font-black text-sm sm:text-base text-white transition-all ${
            isLoading
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-[#c81373] via-rose-600 to-pink-600 hover:from-[#b01065] hover:to-rose-500 active:scale-95 shadow-xl shadow-[#c81373]/30'
          }`}
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin text-white" />
              <span>Canlı Piyasa Taranıyor...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-pink-200" />
              <span>Piyasa Analizini Başlat</span>
            </>
          )}
        </button>

        {/* Dinamik Yükleniyor Adımları */}
        {isLoading && (
          <div className="mt-4 flex items-center gap-2 text-xs text-[#c81373] animate-pulse font-bold text-center px-4">
            <span className="w-2.5 h-2.5 rounded-full bg-[#c81373] shrink-0"></span>
            <span>{loadingMessages[loadingStep]}</span>
          </div>
        )}
      </div>
    </div>
  );
};

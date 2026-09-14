export interface MarketPriceRange {
  min: number;
  average: number;
  max: number;
  currency: string;
}

export interface CompetitorBenchmark {
  platform: string;
  estimatedPrice: number;
  currency: string;
  notes: string;
}

export interface HedefAvmPricingStrategy {
  cashRecommendedPrice: number;
  installmentRecommendedPrice: number;
  monthlyInstallmentPrice: number;
  installmentCount: number;
  suggestedDownPayment: number;
  strategyNote: string;
}

export interface FeasibilityAssessment {
  score: number; // 0 - 100
  verdict: 'GÜÇLÜ SATAR' | 'SATAR (DENGELİ)' | 'DİKKATLİ YAKLAŞILMALI' | 'RİSKLİ / SATMAZ';
  summaryBadge: 'success' | 'warning' | 'danger';
  headline: string;
  reasonsToSell: string[];
  risksAndWatchouts: string[];
  demandLevel: 'Çok Yüksek' | 'Yüksek' | 'Orta' | 'Düşük';
  competitionLevel: 'Çok Yüksek' | 'Yüksek' | 'Orta' | 'Düşük';
  targetAudience: string;
  returnRisk: 'Düşük' | 'Orta' | 'Yüksek';
  seasonalTrend: string;
}

export interface CampaignStrategy {
  title: string;
  campaignType: string;
  description: string;
  bannerSlogan: string;
}

export interface ProductAnalysis {
  id: string;
  createdAt: string;
  productName: string;
  brand: string;
  modelOrCode?: string;
  barcode?: string;
  category: string;
  keyFeatures: string[];
  imagePreview?: string;
  marketPrices: MarketPriceRange;
  competitorBenchmarks: CompetitorBenchmark[];
  hedefPricing: HedefAvmPricingStrategy;
  feasibility: FeasibilityAssessment;
  campaigns: CampaignStrategy[];
  userCost?: number; // Kullanıcının opsiyonel girdiği alış fiyatı
}

export interface AnalyzeApiRequest {
  productName: string; // Zorunlu ürün adı ve modeli
  imageBase64: string;
  mimeType: string;
  additionalNotes?: string;
  userCost?: number;
}

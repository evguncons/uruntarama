import { GoogleGenAI } from '@google/genai';
import { ProductAnalysis } from './types';

export async function analyzeProductImage(
  productName: string,
  imageBase64: string,
  mimeType: string,
  userCost?: number,
  additionalNotes?: string
): Promise<ProductAnalysis> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY ortam değişkeni tanımlanmamış. Lütfen .env.local dosyasını kontrol edin.');
  }

  const ai = new GoogleGenAI({ apiKey });

  // Temizlenmiş base64 string
  const cleanBase64 = imageBase64.replace(/^data:image\/[a-zA-Z0-9+]+;base64,/, '');

  // =========================================================================
  // AŞAMA 1: CANLI GOOGLE SEARCH GROUNDING İLE GÜNCEL PİYASA FİYATLARI
  // (Trendyol, Hepsiburada, Amazon TR, Akakçe, Cimri ve Teknosa/MediaMarkt taranır)
  // =========================================================================
  let liveMarketData = '';
  try {
    const searchResponse = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `Sen Türkiye perakende pazarında uzman bir fiyat araştırmacısısın.
Kullanıcı şu ürünü analiz ediyor: "${productName}".

GÖREVİN:
Google Arama aracını kullanarak Türkiye'deki Akakçe, Cimri, Trendyol, Hepsiburada, Amazon Türkiye, Teknosa ve MediaMarkt sitelerindeki ŞU ANKİ EN GÜNCEL satış fiyatlarını araştır.
1. En ucuz fiyat (TL) ve hangi sitede satıldığı
2. Ortalama piyasa fiyatı (TL)
3. En yüksek yetkili satıcı / mağaza liste fiyatı (TL)
4. Trendyol ve Hepsiburada'daki güncel fiyatlar ve satıcı durumu
5. Ürünün güncel stok/satış durumu (tükenmiş mi, yaygın mı?)

Lütfen gerçek ve güncel rakamları net olarak belirt.`,
      config: {
        tools: [{ googleSearch: {} }],
        temperature: 0.1
      }
    });

    liveMarketData = searchResponse.text || '';
  } catch (searchError) {
    console.warn('Google Search Grounding hatası (fallback mekanizması devreye giriyor):', searchError);
    liveMarketData = `"${productName}" için canlı arama sorgulandı ancak veri anlık olarak doğrudan model tahminine bırakıldı.`;
  }

  // =========================================================================
  // AŞAMA 2: GÖRSEL İNCELEME + GERÇEK PİYASA VERİSİ İLE HEDEF AVM STRATEJİSİ
  // (Yapılandırılmış JSON Raporu)
  // =========================================================================
  const systemInstruction = `Sen Türkiye perakende pazarında uzmanlaşmış, "Hedef AVM" için çalışan kıdemli bir Satın Alma Direktörü ve Fiyatlandırma Stratejistisin.
Hedef AVM; züccaciye, küçük ev aletleri, beyaz eşya, tüketici elektroniği ve mobilya alanında hem peşin hem de Türkiye'ye özgü "elden senetli / taksitli" satış modeliyle çalışan güçlü bir mağazalar zinciridir.

Kullanıcı ürünün tam adını ve modelini belirtmiştir: "${productName}".
Ayrıca ürünün fotoğrafını yüklemiştir.

Aşağıda canlı internet aramasından (Akakçe, Trendyol, Hepsiburada vb.) toplanan en güncel piyasa araştırması verileri yer almaktadır:
--- CANLI PİYASA İSTİHBARATI ---
${liveMarketData}
-------------------------------

GÖREVİN:
Yukarıdaki GERÇEK internet pazar verilerini ve yüklenen fotoğrafı harmanlayarak Hedef AVM için doğrulanmış, gerçekçi bir piyasa fizibilite raporu hazırla.

Fiyatlandırma Kuralları:
1. Pazar fiyatları (min, average, max) yukarıdaki canlı arama sonuçlarındaki gerçek TL rakamlarına dayanmalıdır. Hayali veya eski yıllara ait fiyatlar VERME.
2. Hedef AVM Peşin Satış Fiyatı: Pazaryerleriyle rekabet edebilecek akılcı bir peşin/kredi kartı fiyatı olmalıdır.
3. Hedef AVM Elden Senetli Satış Fiyatı: Elden senetli satışta risk ve vade farkı nedeniyle peşine göre ortalama %20-%35 daha yüksek vadeli toplam fiyat belirlenir. 12 taksite bölünerek aylık taksit tutarı net hesaplanır.
4. "Bu Ürün Satar mı / Satmaz mı?" Karar Motoru: 0-100 arasında net satılabilirlik puanı, somut gerekçeler, pazar riskleri ve mağaza vitrini için vurucu afiş sloganları üret.

ÖNEMLİ: Cevabını SADECE geçerli bir JSON nesnesi olarak döndür. Markdown tırnakları (\`\`\`json) ekleme.`;

  const promptText = `Lütfen "${productName}" ürünü ve görseli için aşağıdaki JSON şemasına BİREBİR uygun yanıt ver:

{
  "productName": "${productName}",
  "brand": "Örn: Apple, Philips, Samsung, Karaca vb.",
  "modelOrCode": "Örn: Model veya seri kodu",
  "barcode": "Varsa barkod veya EAN, yoksa null",
  "category": "Örn: Akıllı Telefonlar, Küçük Ev Aletleri, Züccaciye vb.",
  "keyFeatures": [
    "1. Önemli teknik veya tasarım özelliği",
    "2. Kapasite / Renk / Donanım detayı",
    "3. Öne çıkan müşteri faydası"
  ],
  "marketPrices": {
    "min": (canlı verideki en ucuz TL fiyatı, sayı olarak),
    "average": (canlı verideki ortalama piyasa TL fiyatı, sayı olarak),
    "max": (canlı verideki en yüksek liste TL fiyatı, sayı olarak),
    "currency": "₺"
  },
  "competitorBenchmarks": [
    {
      "platform": "Trendyol",
      "estimatedPrice": (Trendyol güncel TL fiyatı),
      "currency": "₺",
      "notes": "Pazaryeri satıcı durumu ve kargo avantajı"
    },
    {
      "platform": "Hepsiburada",
      "estimatedPrice": (Hepsiburada güncel TL fiyatı),
      "currency": "₺",
      "notes": "Yetkili satıcı / satıcı rekabeti"
    },
    {
      "platform": "Zincir Teknoloji / Perakende Mağazaları",
      "estimatedPrice": (Teknosa/MediaMarkt/AVM mağaza liste fiyatı),
      "currency": "₺",
      "notes": "Fiziki mağaza vitrin fiyatı"
    }
  ],
  "hedefPricing": {
    "cashRecommendedPrice": (Hedef AVM peşin tavsiye satış fiyatı),
    "installmentRecommendedPrice": (Hedef AVM 12 ay elden senetli toplam fiyatı),
    "monthlyInstallmentPrice": (Aylık taksit tutarı: installmentRecommendedPrice / 12),
    "installmentCount": 12,
    "suggestedDownPayment": 0,
    "strategyNote": "Hedef AVM için peşin ve senetli taksitli fiyatlandırma stratejisi notu."
  },
  "feasibility": {
    "score": (0-100 arası satılabilirlik puanı),
    "verdict": "GÜÇLÜ SATAR" | "SATAR (DENGELİ)" | "DİKKATLİ YAKLAŞILMALI" | "RİSKLİ / SATMAZ",
    "summaryBadge": "success" | "warning" | "danger",
    "headline": "Kısa ve net yönetici karar özeti",
    "reasonsToSell": [
      "1. Neden satar somut gerekçe",
      "2. Müşteri talebi ve marka algısı",
      "3. Hedef AVM müşteri profiline uyum"
    ],
    "risksAndWatchouts": [
      "1. Fiyat rekabeti veya stok riski",
      "2. İade veya servis uyarısı"
    ],
    "demandLevel": "Çok Yüksek" | "Yüksek" | "Orta" | "Düşük",
    "competitionLevel": "Çok Yüksek" | "Yüksek" | "Orta" | "Düşük",
    "targetAudience": "Detaylı hedef kitle profili",
    "returnRisk": "Düşük" | "Orta" | "Yüksek",
    "seasonalTrend": "Mevsimsellik ve talep dönemi açıklaması"
  },
  "campaigns": [
    {
      "title": "Kampanya Başlığı",
      "campaignType": "Çeyiz Paketi" | "Günün Fırsatı" | "Elden Senet Kampanyası" | "Özel Fırsat",
      "description": "Kampanya kurgusu ve satış taktiği",
      "bannerSlogan": "Hedef AVM mağaza afişi veya vitrin sloganı"
    },
    {
      "title": "İkinci Kampanya Başlığı",
      "campaignType": "Günün Fırsatı",
      "description": "Alternatif kampanya kurgusu",
      "bannerSlogan": "Sosyal medya veya el ilanı sloganı"
    }
  ]
}

${userCost ? `Kullanıcının belirttiği Alış / Tedarik Maliyeti: ${userCost} ₺. Lütfen Hedef AVM kârlılık ve taksit önerilerini bu maliyeti dikkate alarak oluştur.` : ''}
${additionalNotes ? `Kullanıcıdan Ek Not: "${additionalNotes}"` : ''}`;

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: [
      {
        role: 'user',
        parts: [
          { text: systemInstruction },
          {
            inlineData: {
              data: cleanBase64,
              mimeType: mimeType || 'image/jpeg'
            }
          },
          { text: promptText }
        ]
      }
    ],
    config: {
      responseMimeType: 'application/json',
      temperature: 0.1
    }
  });

  const responseText = response.text || '';
  if (!responseText) {
    throw new Error('Gemini API analiz yanıtı boş döndü. Lütfen tekrar deneyiniz.');
  }

  try {
    const parsed = JSON.parse(responseText);

    const result: ProductAnalysis = {
      id: 'scan_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
      createdAt: new Date().toISOString(),
      productName: parsed.productName || productName,
      brand: parsed.brand || 'Belirtilmemiş',
      modelOrCode: parsed.modelOrCode || undefined,
      barcode: parsed.barcode || undefined,
      category: parsed.category || 'Genel Perakende',
      keyFeatures: Array.isArray(parsed.keyFeatures) ? parsed.keyFeatures : [],
      marketPrices: {
        min: Number(parsed.marketPrices?.min) || 0,
        average: Number(parsed.marketPrices?.average) || 0,
        max: Number(parsed.marketPrices?.max) || 0,
        currency: parsed.marketPrices?.currency || '₺'
      },
      competitorBenchmarks: Array.isArray(parsed.competitorBenchmarks)
        ? parsed.competitorBenchmarks.map((c: any) => ({
            platform: c.platform || 'Pazaryeri',
            estimatedPrice: Number(c.estimatedPrice) || 0,
            currency: c.currency || '₺',
            notes: c.notes || ''
          }))
        : [],
      hedefPricing: {
        cashRecommendedPrice: Number(parsed.hedefPricing?.cashRecommendedPrice) || 0,
        installmentRecommendedPrice: Number(parsed.hedefPricing?.installmentRecommendedPrice) || 0,
        monthlyInstallmentPrice: Number(parsed.hedefPricing?.monthlyInstallmentPrice) || 0,
        installmentCount: Number(parsed.hedefPricing?.installmentCount) || 12,
        suggestedDownPayment: Number(parsed.hedefPricing?.suggestedDownPayment) || 0,
        strategyNote: parsed.hedefPricing?.strategyNote || ''
      },
      feasibility: {
        score: Math.min(100, Math.max(0, Number(parsed.feasibility?.score) || 50)),
        verdict: parsed.feasibility?.verdict || 'SATAR (DENGELİ)',
        summaryBadge:
          (parsed.feasibility?.score || 50) >= 75
            ? 'success'
            : (parsed.feasibility?.score || 50) >= 50
            ? 'warning'
            : 'danger',
        headline: parsed.feasibility?.headline || 'Ürün piyasa talebi orta seviyede.',
        reasonsToSell: Array.isArray(parsed.feasibility?.reasonsToSell) ? parsed.feasibility.reasonsToSell : [],
        risksAndWatchouts: Array.isArray(parsed.feasibility?.risksAndWatchouts) ? parsed.feasibility.risksAndWatchouts : [],
        demandLevel: parsed.feasibility?.demandLevel || 'Orta',
        competitionLevel: parsed.feasibility?.competitionLevel || 'Orta',
        targetAudience: parsed.feasibility?.targetAudience || 'Genel Tüketici',
        returnRisk: parsed.feasibility?.returnRisk || 'Orta',
        seasonalTrend: parsed.feasibility?.seasonalTrend || 'Standart'
      },
      campaigns: Array.isArray(parsed.campaigns)
        ? parsed.campaigns.map((camp: any) => ({
            title: camp.title || 'Kampanya Fırsatı',
            campaignType: camp.campaignType || 'Özel Fırsat',
            description: camp.description || '',
            bannerSlogan: camp.bannerSlogan || ''
          }))
        : [],
      userCost: userCost ? Number(userCost) : undefined
    };

    return result;
  } catch (parseError: any) {
    console.error('Gemini JSON Parse Error:', parseError, 'Raw response:', responseText);
    throw new Error('Gemini API analiz sonucu işlenemedi. Lütfen tekrar deneyiniz.');
  }
}

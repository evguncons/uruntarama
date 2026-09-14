import { GoogleGenAI } from '@google/genai';
import { ProductAnalysis } from './types';

export async function analyzeProductImage(
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

  const systemInstruction = `Sen Türkiye perakende pazarında uzmanlaşmış, "Hedef AVM" için çalışan kıdemli bir Satın Alma Direktörü, Piyasa İstihbarat Uzmanı ve Fiyatlandırma Stratejistisin.
Hedef AVM; züccaciye, küçük ev aletleri, beyaz eşya, ev tekstili, mobilya, kişisel bakım ve tüketici elektroniği alanında hem peşin hem de Türkiye'ye özgü "elden senetli / taksitli" satış modeliyle faaliyet gösteren güçlü bir mağazalar zinciridir.

Görevin:
Kullanıcının yüklediği veya kamerasından çektiği ürün fotoğrafını derinlemesine incelemek, piyasa araştırmasını yapmak ve Hedef AVM yönetiminin hızlı ve karlı satın alma kararı vermesi için kapsamlı bir fizibilite raporu hazırlamaktır.

Analiz Kriterleri:
1. Ürünü tespit et: Marka, model, seri, varsa kutu üzerindeki model kodu/barkod, temel teknik özellikleri.
2. Türkiye Pazar Fiyatları (TRY): Trendyol, Hepsiburada, Amazon TR, N11 ve zincir mağazalardaki güncel piyasa ortalamalarını, en düşük ve en yüksek fiyat aralığını belirle.
3. Hedef AVM Fiyat & Taksit Stratejisi:
   - Peşin/kredi kartı tavsiye satış fiyatı.
   - Elden senetli / 12-15 taksitli tavsiye toplam satış fiyatı (taksitli vadeli fiyat genellikle peşine göre %20-%35 bandında finansman payı içerir).
   - Aylık taksit tutarı ve peşinat önerisi.
4. "Bu Ürün Satar mı / Satmaz mı?" Değerlendirmesi:
   - 0-100 arasında net bir Satılabilirlik Puanı belirle.
   - Net karar: 'GÜÇLÜ SATAR' (80-100), 'SATAR (DENGELİ)' (65-79), 'DİKKATLİ YAKLAŞILMALI' (45-64), 'RİSKLİ / SATMAZ' (0-44).
   - Neden satar? (Somut gerekçeler).
   - Hangi riskler var? (İade riski, rekabet baskısı, servis/yedek parça durumu vb.).
   - Talep düzeyi, rekabet düzeyi, hedef kitle ve mevsimsellik analizi.
5. Kampanya Önerileri: Hedef AVM mağaza içi veya online kanalları için dikkat çekici kampanya başlıkları ve mağaza içi afiş sloganları.

ÖNEMLİ: Cevabını SADECE ve SADECE geçerli bir JSON nesnesi olarak döndür. Markdown tırnakları (\`\`\`json) veya fazladan metin ekleme.`;

  const promptText = `Lütfen fotoğraftaki ürünü analiz et ve aşağıdaki JSON şemasına BİREBİR uygun şekilde yanıt üret:

{
  "productName": "Örn: Philips HD9252/90 Airfryer Fritöz",
  "brand": "Örn: Philips",
  "modelOrCode": "Örn: HD9252/90",
  "barcode": "Varsa barkod veya EAN kodu, yoksa null",
  "category": "Örn: Küçük Ev Aletleri",
  "keyFeatures": [
    "4.1 Litre hazne kapasitesi",
    "Rapid Air sıcak hava teknolojisi",
    "Dijital dokunmatik ekran",
    "Otomatik kapanma ve sıcak tutma"
  ],
  "marketPrices": {
    "min": 2850,
    "average": 3450,
    "max": 4200,
    "currency": "₺"
  },
  "competitorBenchmarks": [
    {
      "platform": "Trendyol",
      "estimatedPrice": 3299,
      "currency": "₺",
      "notes": "Çok satanlarda 1. sırada, yüksek rekabet"
    },
    {
      "platform": "Hepsiburada",
      "estimatedPrice": 3390,
      "currency": "₺",
      "notes": "Hızlı kargo avantajlı satıcılar aktif"
    },
    {
      "platform": "Zincir Teknoloji Mağazaları (Teknosa/MediaMarkt)",
      "estimatedPrice": 3899,
      "currency": "₺",
      "notes": "Mağaza liste fiyatı daha yüksek"
    }
  ],
  "hedefPricing": {
    "cashRecommendedPrice": 3290,
    "installmentRecommendedPrice": 4250,
    "monthlyInstallmentPrice": 354,
    "installmentCount": 12,
    "suggestedDownPayment": 0,
    "strategyNote": "Peşin fiyatı e-ticaret siteleriyle rekabetçi tutulup, asıl kârlılık elden senetli 12 taksit seçeneğiyle yakalanabilir."
  },
  "feasibility": {
    "score": 88,
    "verdict": "GÜÇLÜ SATAR",
    "summaryBadge": "success",
    "headline": "Yüksek popülarite, çeyiz ve günlük kullanımda güçlü talep.",
    "reasonsToSell": [
      "Marka bilinirliği ve güvenilirliği çok yüksek",
      "Hedef AVM müşteri profilinin en çok talep ettiği çeyiz listesi ürünlerinden biri",
      "Senetli taksit imkanı sunulduğunda hızlı devir hızına ulaşır"
    ],
    "risksAndWatchouts": [
      "Online pazaryerlerinde fiyat kırma rekabeti yoğun",
      "Müşteriler internet fiyatını mağazada gösterip indirim isteyebilir"
    ],
    "demandLevel": "Çok Yüksek",
    "competitionLevel": "Yüksek",
    "targetAudience": "Genç çiftler, ev hanımları, çeyiz hazırlığı yapan aileler",
    "returnRisk": "Düşük",
    "seasonalTrend": "Tüm yıl boyunca düzenli talep, Black Friday ve Anneler Günü'nde pik yapar"
  },
  "campaigns": [
    {
      "title": "Muhteşem Çeyiz Fırsatı",
      "campaignType": "Çeyiz Paketi",
      "description": "Tost makinesi ve çay makinesi alanlara bu ürün senetli alımda ekstra %15 indirimle sunulabilir.",
      "bannerSlogan": "Hedef AVM ile Mutfağınızda Şef Sizsiniz! Peşinatsız, Kredi Kartsız Elden Taksitle!"
    },
    {
      "title": "Haftanın Yıldız Ürünü",
      "campaignType": "Günün Fırsatı",
      "description": "Sınırlı stokla peşin fiyatına elden 6 taksit avantajı.",
      "bannerSlogan": "Bu Fiyata Kaçmaz! Hedef AVM'de Günde Sadece Bir Kahve Fiyatına!"
    }
  ]
}

${userCost ? `Kullanıcının belirttiği Alış / Tedarik Maliyeti: ${userCost} ₺. Lütfen Hedef AVM kârlılık önerilerini bu maliyeti dikkate alarak yap.` : ''}
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
      temperature: 0.2
    }
  });

  const responseText = response.text || '';
  if (!responseText) {
    throw new Error('Gemini API yanıtı boş döndü. Lütfen fotoğrafı tekrar çekip deneyiniz.');
  }

  try {
    const parsed = JSON.parse(responseText);

    const result: ProductAnalysis = {
      id: 'scan_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
      createdAt: new Date().toISOString(),
      productName: parsed.productName || 'Bilinmeyen Ürün',
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

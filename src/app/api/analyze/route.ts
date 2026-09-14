import { NextRequest, NextResponse } from 'next/server';
import { analyzeProductImage } from '@/lib/gemini';
import { AnalyzeApiRequest } from '@/lib/types';

export const maxDuration = 60; // 60s timeout for vision model analysis

const ALLOWED_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/heic',
  'image/heif',
  'image/jpg'
];

const MAX_BASE64_LENGTH = 15 * 1024 * 1024; // ~11MB file limit

export async function POST(req: NextRequest) {
  try {
    const contentType = req.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      return NextResponse.json(
        { error: 'Geçersiz istek türü. JSON bekleniyor.' },
        { status: 400 }
      );
    }

    const body: AnalyzeApiRequest = await req.json();

    if (!body.imageBase64 || typeof body.imageBase64 !== 'string') {
      return NextResponse.json(
        { error: 'Lütfen analiz edilecek bir ürün fotoğrafı sağlayın.' },
        { status: 400 }
      );
    }

    if (body.imageBase64.length > MAX_BASE64_LENGTH) {
      return NextResponse.json(
        { error: 'Görsel boyutu çok büyük (Maksimum 10MB olmalıdır). Lütfen görseli küçültüp tekrar deneyin.' },
        { status: 413 }
      );
    }

    const mimeType = body.mimeType || 'image/jpeg';
    if (!ALLOWED_MIME_TYPES.includes(mimeType.toLowerCase())) {
      return NextResponse.json(
        { error: `Desteklenmeyen dosya biçimi: ${mimeType}. Yalnızca JPG, PNG ve WEBP formatları desteklenmektedir.` },
        { status: 415 }
      );
    }

    // Kullanıcı maliyeti kontrolü
    let userCost: number | undefined = undefined;
    if (body.userCost !== undefined && body.userCost !== null && !isNaN(Number(body.userCost))) {
      userCost = Math.max(0, Number(body.userCost));
    }

    const notes = body.additionalNotes?.slice(0, 500); // 500 karakter sınır

    // Gemini analizi çalıştır
    const analysis = await analyzeProductImage(
      body.imageBase64,
      mimeType,
      userCost,
      notes
    );

    return NextResponse.json(
      {
        success: true,
        data: analysis
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error('Analyze API Error:', error);

    const errorMessage = error?.message || 'Bilinmeyen bir hata oluştu.';

    // Gemini API spesifik hata mesajları
    if (errorMessage.includes('API_KEY')) {
      return NextResponse.json(
        { error: 'Sistemde geçerli bir GEMINI_API_KEY bulunamadı. Lütfen yöneticinize başvurun.' },
        { status: 500 }
      );
    }

    if (errorMessage.includes('RESOURCE_EXHAUSTED') || errorMessage.includes('429')) {
      return NextResponse.json(
        { error: 'Gemini API anlık istek kotası aşıldı. Lütfen 30 saniye sonra tekrar deneyiniz.' },
        { status: 429 }
      );
    }

    return NextResponse.json(
      { error: `Analiz sırasında bir sorun oluştu: ${errorMessage}` },
      { status: 500 }
    );
  }
}

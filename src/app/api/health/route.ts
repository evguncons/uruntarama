import { NextResponse } from 'next/server';

export async function GET() {
  const hasKey = Boolean(process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY.length > 10);
  return NextResponse.json({
    status: 'ok',
    service: 'Hedef AVM Ürün Piyasa Analiz AI',
    geminiConfigured: hasKey,
    timestamp: new Date().toISOString()
  });
}

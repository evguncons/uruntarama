/**
 * İstemci tarafında görselleri optimize eder, aşırı büyük mobil fotoğrafları
 * kaliteli şekilde küçülterek veri kotasını korur ve analizi hızlandırır.
 */
export async function optimizeImageFile(
  file: File,
  maxDimension = 1600,
  quality = 0.85
): Promise<{ base64: string; mimeType: string; previewUrl: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Canvas context oluşturulamadı.'));
          return;
        }

        // Yumuşak ölçekleme
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, 0, 0, width, height);

        const mimeType = 'image/jpeg';
        const base64 = canvas.toDataURL(mimeType, quality);

        resolve({
          base64,
          mimeType,
          previewUrl: base64
        });
      };

      img.onerror = () => {
        reject(new Error('Görsel dosyası yüklenemedi veya bozuk.'));
      };

      img.src = e.target?.result as string;
    };

    reader.onerror = () => {
      reject(new Error('Dosya okunamadı.'));
    };

    reader.readAsDataURL(file);
  });
}

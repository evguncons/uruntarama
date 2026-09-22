"""Product Matching Engine with GTIN, Model, Variant and Confidence scoring."""
import re
import unicodedata
from typing import Optional, Dict, Any, Tuple

def normalize_text(val: str) -> str:
    """Lowercase and remove Turkish diacritics."""
    if not val:
        return ""
    val = str(val).lower().replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return ''.join(c for c in unicodedata.normalize('NFKD', val) if not unicodedata.combining(c))

class ProductMatcher:
    ACCESSORY_PATTERN = re.compile(
        r'\b(kilif|ekran koruyucu|nano cam|lens koruma|kamera koruma|sarj aleti|sarj cihazi|type-c kablo|kapak|kulaklik kilifi|stand|tutucu)\b',
        re.I
    )

    CRITICAL_SUFFIXES = ('pro', 'plus', 'ultra', 'fe', 'max', 'lite', 'se', 'mini')

    KNOWN_BRANDS = {
        'philips', 'samsung', 'apple', 'dyson', 'arcelik', 'beko', 'vestel',
        'xiaomi', 'redmi', 'poco', 'karaca', 'tefal', 'bosch', 'siemens',
        'delonghi', 'roborock', 'gm', 'generalmobile', 'huawei', 'honor',
        'lenovo', 'asus', 'hp', 'dell', 'sony', 'lg', 'fakir', 'braun'
    }

    @classmethod
    def is_accessory(cls, title: str, query: str) -> bool:
        norm_title = normalize_text(title)
        norm_query = normalize_text(query)
        if cls.ACCESSORY_PATTERN.search(norm_title) and not cls.ACCESSORY_PATTERN.search(norm_query):
            return True
        return False

    @classmethod
    def extract_model_codes(cls, text: str) -> set:
        """Extract alphanumeric model identifiers and standalone model numbers."""
        norm = normalize_text(text)
        compact = lambda x: re.sub(r'[^a-z0-9]', '', x)
        raw_matches = re.findall(r'([a-z]+)[\s-]*(\d+)([a-z0-9]*)', norm)
        codes = set()
        for prefix, num, suffix in raw_matches:
            if prefix in cls.KNOWN_BRANDS:
                codes.add(num)
            elif prefix not in ('pro', 'plus', 'ultra', 'fe', 'max', 'lite', 'ram', 'gb', 'tb', 'kg', 'mah', 'watt', 'g'):
                codes.add(compact(prefix + num + suffix))
                codes.add(num)
        for num in re.findall(r'\b\d{3,5}\b', norm):
            codes.add(num)
        return codes

    @classmethod
    def evaluate(cls, expected: str, detected_title: str, detected_gtin: Optional[str] = None, expected_gtin: Optional[str] = None) -> Tuple[bool, float, str]:
        """
        Returns (is_match, confidence, reason).
        1.00 = exact
        0.90+ = very high
        0.75-0.89 = possible / good
        <0.75 = unreliable / mismatch
        """
        if not expected or not detected_title:
            return False, 0.0, "Eksik ürün adı"

        # GTIN/EAN exact match has priority 1
        if expected_gtin and detected_gtin:
            if str(expected_gtin).strip() == str(detected_gtin).strip():
                return True, 1.0, "GTIN/EAN tam eşleşti"

        if cls.is_accessory(detected_title, expected):
            return False, 0.0, "Aksesuar tespit edildi (cihazın kendisi değil)"

        q_norm = normalize_text(expected)
        t_norm = normalize_text(detected_title)

        # 1. Critical Suffix Check (Pro, Plus, Ultra, FE, Max, Lite)
        for suffix in cls.CRITICAL_SUFFIXES:
            suffix_pattern = r'(?:\b' + suffix + r'\b|[a-z]+\d+' + suffix + r'\b)'
            q_has = bool(re.search(suffix_pattern, q_norm))
            t_has = bool(re.search(suffix_pattern, t_norm))
            if q_has != t_has:
                return False, 0.30, f"Model eki uyuşmuyor: '{suffix}' beklendi/bulundu farkı"

        # 2. Capacity Check (128gb, 256gb, 512gb, 1tb)
        q_caps = re.findall(r'\b(\d+)\s*(?:gb|tb)\b', q_norm)
        t_caps = re.findall(r'\b(\d+)\s*(?:gb|tb)\b', t_norm)
        if q_caps and t_caps:
            if not any(c in t_caps for c in q_caps):
                return False, 0.40, f"Kapasite/hafıza uyuşmuyor: Beklenen {q_caps}, Tespit edilen {t_caps}"

        # 3. Model Code Check
        expected_codes = cls.extract_model_codes(q_norm)
        detected_codes = cls.extract_model_codes(t_norm)

        if expected_codes:
            def code_matches(expected_code):
                return any(
                    detected == expected_code or
                    expected_code in detected or
                    detected in expected_code or
                    any(detected == expected_code + suffix for suffix in cls.CRITICAL_SUFFIXES) or
                    re.search(r'\b' + re.escape(expected_code) + r'\b', t_norm)
                    for detected in detected_codes
                ) or bool(re.search(r'\b' + re.escape(expected_code) + r'\b', t_norm))

            if not all(code_matches(c) for c in expected_codes):
                return False, 0.50, f"Model kodu uyuşmuyor: Beklenen {expected_codes}, Bulunan {detected_codes}"

        # 4. Token Overlap Scoring
        q_tokens = set(re.findall(r'[a-z0-9]{2,}', q_norm))
        t_tokens = set(re.findall(r'[a-z0-9]{2,}', t_norm))

        # Filter out common stop words
        stop_words = {'akilli', 'telefon', 'cep', 'telefonu', 'ceptelefonu', 'garantili', 'turkiye', 'tr', 'resmi', 'distributor', 'fiyati', 'en', 'ucuz'}
        q_tokens = {t for t in q_tokens if t not in stop_words}
        t_tokens = {t for t in t_tokens if t not in stop_words}

        if not q_tokens:
            return True, 0.80, "Temel eşleşme sağlandı"

        overlap_count = 0
        for qt in q_tokens:
            if any(qt == tt or (len(qt) >= 4 and qt in tt) for tt in t_tokens):
                overlap_count += 1
        ratio = overlap_count / len(q_tokens) if q_tokens else 1.0

        if ratio >= 0.85:
            confidence = 0.95
        elif ratio >= 0.65:
            confidence = 0.85
        elif ratio >= 0.50:
            confidence = 0.75
        else:
            confidence = 0.60

        is_match = confidence >= 0.75
        reason = f"Model ve varyant doğrulandı (%{int(confidence*100)} eşleşme)" if is_match else f"Yetersiz eşleşme (%{int(confidence*100)})"
        return is_match, confidence, reason

    @classmethod
    def match_product(cls, expected: str, detected_title: str, detected_gtin: Optional[str] = None, expected_gtin: Optional[str] = None) -> Tuple[float, list]:
        """Convenience method returning (confidence, reasons_list)."""
        is_match, confidence, reason = cls.evaluate(expected, detected_title, detected_gtin, expected_gtin)
        return confidence, [reason]

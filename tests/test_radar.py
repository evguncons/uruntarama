import json
import unittest
from unittest.mock import patch
from radar import direct_url, model_matches, money, parse_page, verify_one, STORES

URL = 'https://www.trendyol.com/general-mobile/gm26-pro-p-123456789'

def page(name='GM 26 Pro 256GB', price='22880.00', stock='InStock', extra=''):
    product = {'@type': 'Product', 'name': name, 'offers': {'@type': 'Offer', 'price': price, 'priceCurrency': 'TRY', 'availability': 'https://schema.org/' + stock}}
    return '<h1>' + name + '</h1><script type="application/ld+json">' + json.dumps(product) + '</script><main>' + extra + '</main>'

class RadarTests(unittest.TestCase):
    def test_prices_are_not_rounded_or_rescaled(self):
        r = parse_page('GM26 Pro', 'trendyol', URL, page(price='39598.75'))
        self.assertEqual(r['price'], 39598.75)
        self.assertTrue(r['isAvailable'])

    def test_notification_overrides_schema_stock(self):
        r = parse_page('GM26 Pro', 'trendyol', URL, page(extra='Gelince Haber Ver'))
        self.assertEqual(r['status'], 'out_of_stock')
        self.assertIsNone(r['price'])
        self.assertEqual(r['productUrl'], URL)

    def test_hidden_notice_not_stock(self):
        r = parse_page('GM26 Pro', 'trendyol', URL, page(extra='<div style="display:none">Stokta yok</div>'))
        self.assertEqual(r['status'], 'in_stock')

    def test_unknown_is_not_out_of_stock(self):
        r = parse_page('GM26 Pro', 'trendyol', URL, '<h1>GM26 Pro</h1>')
        self.assertEqual(r['status'], 'unverified')
        self.assertIsNone(r['isAvailable'])
        self.assertIsNone(r['price'])

    def test_model_mismatch(self):
        self.assertTrue(model_matches('GM26 Pro 256GB', 'General Mobile GM 26 Pro 5G 256 GB'))
        for name in ('GM 26 128GB', 'GM 26 Pro kılıf', 'GM 26 Pro 128GB', 'GM 260 Pro 256GB'):
            r = parse_page('GM26 Pro 256GB', 'trendyol', URL, page(name=name))
            self.assertEqual(r['productUrl'], '', name)
            self.assertIsNone(r['price'])

    def test_category_redirect_and_domains_rejected(self):
        for url, key in [('https://www.cimri.com/cep-telefonlari','cimri'), ('https://www.trendyol.com/sr?q=gm26','trendyol'), ('https://trendyol.com.evil.test/gm26-p-1234567','trendyol'), ('https://vertexaisearch.cloud.google.com/grounding-api-redirect/123','official')]:
            self.assertFalse(direct_url(url, key))
        self.assertNotIn('n11', STORES)
        self.assertNotIn('teknosa', STORES)
        self.assertTrue(direct_url('https://www.cimri.com/cep-telefonlari/en-ucuz-gm26-pro-fiyatlari%2Ca2562232095', 'cimri'))

    def test_access_failure_never_publishes_price_or_link(self):
        with patch('radar.fetch_page', side_effect=ValueError('404')):
            row = verify_one('GM26 Pro', 'trendyol', [URL])
        self.assertIsNone(row['price'])
        self.assertIsNone(row['isAvailable'])
        self.assertEqual(row['productUrl'], '')

    def test_money_formats(self):
        self.assertEqual(money('23.499,00 TL'), 23499)
        self.assertEqual(money('23499.00'), 23499)
        self.assertEqual(money('22.880 TL'), 22880)

    def test_aggregate_offer_not_seller_price(self):
        html = page().replace('"@type": "Offer"', '"@type": "AggregateOffer"')
        self.assertIsNone(parse_page('GM26 Pro', 'trendyol', URL, html)['price'])

    def test_official_variant_stock_is_scoped(self):
        html = '<h1>GM26 Pro</h1><div class="payment-1" id="one"><span>512GB</span><small class="money_payment">27999</small>Stokta Yok</div><div class="payment-1" id="two"><span>256GB</span><small class="money_payment">26999</small><a onclick="SetSelectedProductIds(1)">Devam</a></div>'
        r = parse_page('GM26 Pro', 'official', 'https://www.generalmobile.com/tr/gm26pro5g/model', html)
        self.assertEqual(r['price'], 26999)
        self.assertTrue(r['productUrl'].endswith('#two'))
        r = parse_page('GM26 Pro 512GB', 'official', 'https://www.generalmobile.com/tr/gm26pro5g/model', html)
        self.assertEqual(r['status'], 'out_of_stock')
        self.assertIsNone(r['price'])

    def test_yon_notification_overrides_other_buy_buttons(self):
        html = page(extra='<a id="aGelinceHaberVer">Gelince Haber Ver</a><button>Sepete ekle</button>')
        row = parse_page('GM26 Pro', 'yonavm', 'https://www.yonavm.com.tr/gm26-pro-11269', html)
        self.assertEqual(row['status'], 'out_of_stock')
        self.assertIsNone(row['price'])

if __name__ == '__main__':
    unittest.main()

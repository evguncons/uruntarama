import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from radar import GM26_HINTS, fetch_page, parse_page

out = Path('test-artifacts')
out.mkdir(exist_ok=True)
rows = []
urls = dict(GM26_HINTS, taspinar='https://taspinar.com/general-mobile-gm-26-8-128gb-5g-black-p-1552020185', cimri='https://www.cimri.com/cep-telefonlari')
for key, url in urls.items():
    try:
        final, html = fetch_page(url, key)
        (out / (key + '.html')).write_text(html, encoding='utf-8')
        row = parse_page('GM26 Pro', key, final, html)
    except Exception as e:
        row = {'key': key, 'status': 'fetch_failed', 'error': str(e)}
    rows.append(row)
    print(json.dumps(row, ensure_ascii=True), flush=True)
(out / 'gm26-pro.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')

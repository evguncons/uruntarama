"""Bounded public-page transport. Resolve once and connect to that public IP.

No credentials, cookies, proxy, CAPTCHA bypass, or private network access.
Redirects retain the merchant hostname (www aliases are allowed).
"""
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urlsplit, urljoin


def host_key(url):
    return (urlsplit(url).hostname or '').lower().removeprefix('www.')


def public_address(url):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError('Invalid public URL')
    if p.port not in (None, 80, 443) or any(c in url for c in '\r\n\\'):
        raise ValueError('Invalid port or URL')
    addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Non-public address')
    return addresses[0][4][0]


def fetch_page(url, timeout=10, max_bytes=4 * 1024 * 1024):
    original = url
    deadline = time.monotonic() + 25
    for hop in range(6):
        p = urlsplit(url)
        if host_key(url) != host_key(original):
            return {'code': 0, 'final_url': url, 'html': '', 'error': 'INVALID_URL'}
        for attempt in range(2):
            conn = None
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                address = public_address(url)
                port = p.port or (443 if p.scheme == 'https' else 80)
                # Pin the checked address: TLS still authenticates the original host.
                conn = http.client.HTTPConnection(p.hostname, port, timeout=min(timeout, remaining))
                raw = socket.create_connection((address, port), timeout=min(timeout, remaining))
                conn.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=p.hostname) if p.scheme == 'https' else raw
                conn.request('GET', (p.path or '/') + ('?' + p.query if p.query else ''), headers={
                    'Host': p.netloc, 'User-Agent': 'ProductRadar/1.0',
                    'Accept': 'text/html,application/json', 'Accept-Encoding': 'identity',
                })
                res = conn.getresponse()
                if res.status == 429 and attempt == 0:
                    delay = res.getheader('Retry-After', '1')
                    time.sleep(min(2, float(delay)) if delay.isdigit() else 1)
                    continue
                if res.status in (301, 302, 303, 307, 308):
                    target = res.getheader('Location')
                    if not target or hop == 5:
                        raise ValueError('Invalid redirect')
                    url = urljoin(url, target)
                    break
                body = res.read(max_bytes + 1)
                if len(body) > max_bytes or res.getheader('Content-Encoding', 'identity') != 'identity':
                    raise ValueError('Unsupported response size/encoding')
                charset = res.headers.get_content_charset() or 'utf-8'
                return {'code': res.status, 'final_url': url, 'html': body.decode(charset, errors='replace'), 'error': None}
            except (socket.timeout, TimeoutError):
                if attempt == 1:
                    return {'code': 0, 'final_url': url, 'html': '', 'error': 'TIMEOUT'}
            except (OSError, http.client.HTTPException):
                if attempt == 1:
                    return {'code': 0, 'final_url': url, 'html': '', 'error': 'UNKNOWN'}
            except (ValueError, LookupError):
                return {'code': 0, 'final_url': url, 'html': '', 'error': 'INVALID_URL'}
            finally:
                if conn:
                    conn.close()
    return {'code': 0, 'final_url': url, 'html': '', 'error': 'UNKNOWN'}

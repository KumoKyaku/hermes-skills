# JAV Search & Download Reference

## sukebei.nyaa.si — URL Structure

Base: `https://sukebei.nyaa.si/`

Search:
```
/?q={CODE}&f=0&c=0_0&s=seeders&o=desc
```

| Parameter | Value | Meaning |
|-----------|-------|---------|
| q | JAV code (e.g. KAWD-722) | Search query |
| f | 0 | All filters off |
| c | 0_0 | All categories |
| s | seeders | Sort by seeders |
| o | desc | Descending order |

## Magnet Link Extraction

```python
import requests, re

proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(f'https://sukebei.nyaa.si/?q={CODE}&f=0&c=0_0&s=seeders&o=desc',
                 headers=headers, proxies=proxies, timeout=15)

# Extract magnets
magnets = re.findall(r'href="(magnet:\?xt=urn:btih:[a-zA-Z0-9]+[^"]*)"', r.text)

# Extract size/seeders from table rows
rows = re.findall(r'<tr[^>]*>.*?</tr>', r.text, re.DOTALL)
for row in rows:
    if 'magnet:' not in row:
        continue
    magnet = re.search(r'href="(magnet:[^"]+)"', row)
    size = re.search(r'<td class="text-center"[^>]*>([\d.]+ (?:MiB|GiB))</td>', row)
    tds = re.findall(r'<td[^>]*class="text-center"[^>]*>(\d+)</td>', row)
    seeders = tds[-2] if len(tds) >= 2 else "?"
```

## Best Practice Flow

1. Start mihomo proxy via terminal(background=true)
2. Search sukebei via Python with proxy
3. Present user with version options (去码版 > H265 > 原盘)
4. Start aria2c download in background with proxy
5. Once peers connect, can optionally kill proxy to save VPN traffic
6. Download to E:/SystemCacheInfo/Others/
7. Report completion with file path and size

## Common JAV Codes Format

Standard: `XXX-NNN` where XXX is the studio prefix and NNN is the number.
Examples: KAWD-722, ABP-923, CSCT-002

## Proxy Requirement

All JAV sites (sukebei, javdb, javbus, javlibrary) are GFW-blocked from China.
Always use mihomo proxy when searching for or downloading JAV content.
The aria2c download itself may also need proxy for tracker communication.

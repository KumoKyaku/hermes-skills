# CDN Manga Image Extraction (1kkk.com / dm5.com)

## Site Structure

1kkk.com (极速漫画) and dm5.com share the same engine. Gallery URLs:
```
https://cnc.1kkk.com/other<CID>/
https://tel.dm5.com/other<CID>/
```

## JavaScript Variables (in page HTML)

```javascript
var DM5_MID = 88718;          // Manga ID (89 = account, 88718 = manga)
var DM5_CID = 1606385;        // Chapter ID
var DM5_IMAGE_COUNT = 8;      // Number of images
var DM5_CTITLE = "月村手毬";   // Chapter title
var DM5_USERID = 0;
var DM5_PAGETYPE = 9;
var DM5_READMODEL = 1;
```

Extract via Python:
```python
import re
cid = re.search(r"DM5_CID\s*=\s*(\d+)", html).group(1)
count = re.search(r"DM5_IMAGE_COUNT\s*=\s*(\d+)", html).group(1)
```

## CDN Image URL Pattern

The CDN host is `manhua{N}.cdndm5.com` where N varies per session. Full URL structure:

```
https://{CDN_HOST}/89/{MID}/{CID}/{PAGE}_{RANDOM}.jpg?cid={CID}&key={KEY}
```

Example:
```
https://manhua1039-61-174-50-98.cdndm5.com/89/88718/1606385/1_4138.jpg?cid=1606385&key=a4f37c97703742e4226cd2e0db62f958
```

Components:
- `89/88718/` — account/manga path (fixed per manga)
- `1606385/` — chapter ID
- `1_4138.jpg` — page number (`1`) + random suffix (`4138`)
- `?cid=1606385&key=...` — auth parameters

## Extracting Image URLs (Browser Console)

The CDN requires browser context (cookies/referer). Navigate to each page via browser:

```javascript
// On any page, get the manga image details:
(() => {
  let imgs = document.querySelectorAll('img');
  for(let img of imgs) {
    if(img.src && img.src.includes('manhua')) {
      let url = new URL(img.src);
      return JSON.stringify({
        src: url.href,
        host: url.host,
        path: url.pathname,
        key: url.searchParams.get('key'),
        cid: url.searchParams.get('cid')
      });
    }
  }
  return 'no image found';
})()
```

Key observations:
- **Host** stays the same across all pages of a chapter
- **Key** stays the same across all pages of a chapter
- **Random suffix** changes per page (not predictable)
- You must navigate to each page to discover each page's URL

## Direct Download Limitation

Curl/Python requests to the CDN fail with `ConnectionResetError (10054)`:
- The CDN checks `Referer` header AND browser session cookies
- Even with correct `Referer: https://cnc.1kkk.com/other{CID}/`, the TLS handshake is rejected
- **Must use browser context** for the download

## Alternative: Browser Vision Screenshots

If image download fails, take screenshots of each page with `browser_vision`. Resolution is ~1200x1678 for manga pages — readable but not archival quality.

## Chapter List Discovery

Chapters are linked in the page HTML as `<a>` tags:
```html
<a href="/other1606385/">月村手毬</a>
<a href="/other1606386/">有村麻央</a>
<a href="/other1606387/">篠泽广</a>
```

Extract all chapters with Python:
```python
chapters = re.findall(r'other(\d+)/[^>]*>([^<]+)</a>', html)
# Returns: [('1606385', '月村手毬'), ('1606386', '有村麻央'), ...]
```

---
name: torrent-download
title: Torrent & Magnet Download
description: Download torrents/magnets via aria2c on Windows, with mihomo proxy for GFW-blocked trackers. JAV/doujinshi search workflow included.
version: 1.1.0
tags: [aria2c, torrent, magnet, bittorrent, download, proxy, mihomo, sukebei]
---

# Torrent & Magnet Download

Download magnet links and torrent files on Windows.

## ⚠️ 首选工具：Free Download Manager (FDM)，不是 aria2c

**用户明确要求：FDM 优先，不用 aria2c。**（2026-08 确认）

原因（实战教训）：
1. GFW 对 BT 数据流做 DPI 深度包检测 — aria2c 即使连上大量 peer（CN:50-80），`DL:0B` 持续，数据流被掐
2. aria2c 失败时会留下 0 字节占位的嵌套空壳目录 + `.aria2` 残留文件，污染下载目录
3. FDM 下载琉璃神社 11-12GiB 月度合集稳定成功（04/05/06 月合集均为 FDM 下载）

**FDM 流程**（琉璃神社月合集见 `references/liuli-monthly-collection.md`）：
```bash
# FDM 是 GUI 程序：必须 background 启动（前台会卡到超时）
terminal(background=true, command="cd '/d/Program Files/Softdeluxe/Free Download Manager' && ./fdm.exe '<magnet>'")
```
- FDM 收到 magnet 后会**弹窗等待用户确认保存路径**（任务不会自动进队列）
- 需要用户手动：确认保存路径 → 点下载

**aria2c 仅作为最后手段**（上面 FDM 不可用/用户要求时才用，见下方 Workflow）。

## Prerequisites

- **FDM**: `D:\Program Files\Softdeluxe\Free Download Manager\fdm.exe`（首选）
- **aria2c**（备选）: installed via `winget install aria2.aria2 --silent` → `C:\Users\<user>\AppData\Local\Microsoft\WinGet\Links\aria2c`
- **mihomo** (optional): for accessing GFW-blocked trackers/sites. Path: `OneDrive/翻墙/v2rayN-windows-64/bin/mihomo/mihomo.exe`, config: `OneDrive/翻墙/Clash_1777610321.yaml`
- **Default save directory**: `E:/SystemCacheInfo/Others/`

## Workflow

### 1. Search for content

For JAV codes or doujinshi, search on **sukebei.nyaa.si** (requires proxy):

```bash
curl -x http://127.0.0.1:7890 -s --compressed --max-time 20 \
  "https://sukebei.nyaa.si/?q=<URL_ENCODED_QUERY>&f=0&c=0_0&s=seeders&o=desc" \
  -H "User-Agent: Mozilla/5.0"
```

Extract magnet links from the HTML:
```python
import re, urllib.parse
magnets = re.findall(r'href="(magnet:\?xt=urn:btih:[a-zA-Z0-9]+[^\"]*)"', html)
for m in magnets:
    dn = re.search(r'dn=([^&]+)', m)
    if dn:
        title = urllib.parse.unquote(dn.group(1))
```

### 2. Start proxy (if needed)

```bash
/c/Users/Sun47/OneDrive/翻墙/v2rayN-windows-64/bin/mihomo/mihomo.exe \
  -f "/c/Users/Sun47/OneDrive/翻墙/Clash_1777610321.yaml"
```

Wait 8-15 seconds for initialization, then verify:
```bash
curl -x http://127.0.0.1:7890 -s --max-time 10 http://httpbin.org/ip
```

### 3. Download with aria2c

**Without proxy (direct):**

Start with NO proxy — HTTP trackers work from China and peer connections go direct, avoiding GFW interference with UDP:

```bash
cd "/e/SystemCacheInfo/Others"
aria2c --seed-time=0 \
  --bt-tracker="http://sukebei.tracker.wf:8888/announce,http://tracker.tasvideos.org:6969/announce,http://tracker.bt4g.com:2095/announce,http://tracker2.itzmx.com:6961/announce,udp://tracker.opentrackr.org:1337/announce,udp://tracker.openbittorrent.com:6969/announce" \
  --max-connection-per-server=16 --split=16 --bt-max-peers=100 \
  "<magnet_or_torrent>"
```

If CN:0 persists, download the .torrent file first (via proxy) and use it instead of magnet:

```bash
cd "/e/SystemCacheInfo/Others"
aria2c --seed-time=0 \
  --bt-tracker="http://sukebei.tracker.wf:8888/announce,http://tracker.tasvideos.org:6969/announce,http://tracker.bt4g.com:2095/announce,http://tracker2.itzmx.com:6961/announce" \
  --max-connection-per-server=16 --split=16 --bt-max-peers=100 \
  "<name>.torrent"
```

**With proxy (for tracker announces only):**

⚠️ **NEVER use `--all-proxy` with BitTorrent.** `--all-proxy` routes ALL traffic (including peer-to-peer BitTorrent TCP connections) through the HTTP proxy — but HTTP proxies cannot tunnel raw BitTorrent protocol, causing `CN:0`. Instead:

- Use proxy **only** to query trackers for peer lists (via curl)
- Connect to peers **directly** (no proxy)
- Use HTTP trackers (not UDP — those get blocked by GFW)

```bash
# Step 1: Download torrent file via proxy (sukebei is blocked in China)
curl -x http://127.0.0.1:7890 -sL --max-time 30 \
  "https://sukebei.nyaa.si/download/<ID>.torrent" \
  -o "<name>.torrent"

# Step 2: Download with NO proxy — HTTP trackers work from China,
# peer connections go direct
aria2c --seed-time=0 \
  --bt-tracker="http://sukebei.tracker.wf:8888/announce,http://tracker.tasvideos.org:6969/announce,http://tracker.bt4g.com:2095/announce,http://tracker2.itzmx.com:6961/announce" \
  --max-connection-per-server=16 --split=16 --bt-max-peers=100 \
  "<name>.torrent"
```

### 4. Check download progress

Use `process(action='poll')` or `process(action='log')` to check.
Use `process(action='wait')` to block until progress appears.

### 5. Fallback: Chinese manga mirror sites (when BT has no seeds / proxy dead)

When sukebei.nyaa.si is inaccessible (proxy nodes expired) or the torrent has 0 seeders:

**Step 1: Search Chinese manga sites via 360搜索**

360搜索 (so.com) is accessible from China without proxy. Search for the doujinshi title:
```bash
# Browser navigation works best (handles redirects)
browser_navigate(url="https://www.so.com/s?q=角砂糖+学マス+結婚生活合同+結")

# Or use curl + Python to parse results
python -c "
import urllib.request, re
query = urllib.parse.urlencode({'q': '角砂糖 学マス 結婚生活合同'})
resp = urllib.request.urlopen('https://www.so.com/s?' + query, timeout=15)
html = resp.read().decode('utf-8', errors='replace')
# Extract links from search results
results = re.findall(r'<a[^>]*href=\"(https://[^\"]+)\"[^>]*>(.*?)</a>', html)
"
```

**Known Chinese manga mirror sites:**
- `cnc.1kkk.com` / `tel.dm5.com` — 极速漫画, large doujinshi collection
- `www.1kkk.com` — main domain

**Step 2: Find the gallery on the mirror site**

Look for the `other<ID>/` URL pattern on 1kkk.com. Multiple chapters per work:
```
https://cnc.1kkk.com/other1606385/  → 月村手毬 (8 images)
https://cnc.1kkk.com/other1606386/  → 有村麻央 (6 images)
https://cnc.1kkk.com/other1606387/  → 篠泽广 (12 images)
...
```

Chapter info is embedded in the HTML as JavaScript variables:
```javascript
var DM5_MID=88718;          // Manga ID
var DM5_CID=1606385;        // Chapter ID  
var DM5_IMAGE_COUNT=8;      // Number of images
var DM5_CTITLE="月村手毬";  // Chapter title
```

**Step 3: Extract image URLs from the browser**

The CDN (cdndm5.com) requires browser context (cookies/referer). Direct curl/Python download fails with connection reset. Use browser console to extract each page's image URL:

```javascript
// In browser console, after navigating to a page:
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
})()
```

Output gives you the CDN host, chapter path, and auth key. Then navigate to each page number to get the image URL for that page. The key and host stay the same across pages of a single chapter.

**CDN image URL pattern:**
```
https://{cdn_host}/89/{mid}/{cid}/{page}_{random}.jpg?cid={cid}&key={key}
```

**Step 4: Download images via browser**

Since direct download fails, the best approach is to use the browser to navigate each page sequentially, extract the image URL from the console, and save via download.

Alternative: Use the browser console `fetch()` in the page context (which has proper cookies):
```javascript
fetch(img.src).then(r => r.blob()).then(b => {
  let a = document.createElement('a');
  a.href = URL.createObjectURL(b);
  a.download = 'page.jpg';
  a.click();
})
```

### 6. Cleanup

**Always kill mihomo proxy after download to save monthly traffic (50GB cap):**
```bash
taskkill //F //IM mihomo.exe
```

**Always deliver the file to the user when done.** Use `MEDIA:/path/to/file` to send images or files.

## Common Search Queries

| Type | Query Pattern |
|------|---------------|
| JAV by code | `KAWD-722` → `?q=KAWD-722` |
| Doujinshi by title/character | `学マス 同人誌` → `?q=%E5%AD%A6%E3%83%9E%E3%82%B9+%E5%90%8C%E4%BA%BA%E8%AA%8C` |
| Full game name | `学園アイドルマスター 同人誌` → more results than short name |
| Chinese mirror site search | Use 360搜索 (so.com) with Chinese terms, e.g. `角砂糖 学マス 结婚生活合同` |

## BT Proxy Nodes (mihomo Config)

The mihomo config has **dedicated proxy nodes** for BitTorrent traffic, using Hysteria2 protocol with port hopping:

| Node name | Type | Port range | Description |
|-----------|------|------------|-------------|
| `🇺🇦 bt下载-乌克兰h-0.5倍率` | Hysteria2 | 25300-26300 | 0.5x traffic, UDP enabled, 30s hop interval |
| `🇺🇦 bt下载-乌克兰-VIP88` | VLESS | 11574 | VIP node, UDP enabled |
| `🇺🇦 bt下载-乌克兰-VIP88a` | anytls | 11697 | Alternative VIP node |
| `🇺🇦 2倍率-bt下载-乌克兰` | (listed) | — | 2x traffic, last resort |

These nodes use a different protocol (Hysteria2) designed for UDP-heavy workloads like BitTorrent. To force all traffic through a BT node:

```bash
# Generate a temp config with BT node as default
cp "/c/Users/Sun47/OneDrive/翻墙/Clash_1777610321.yaml" "/c/Users/Sun47/OneDrive/翻墙/Clash_bt.yaml"

# Use PowerShell to avoid Python3 encoding issues in git-bash
powershell.exe -Command \
  "(Get-Content 'C:\Users\Sun47\OneDrive\翻墙\Clash_bt.yaml') -replace '♻️自动选择', '🇺🇦 bt下载-乌克兰h-0.5倍率' | \
   Set-Content 'C:\Users\Sun47\OneDrive\翻墙\Clash_bt.yaml'"

# Start mihomo with temp config
/c/Users/Sun47/OneDrive/翻墙/v2rayN-windows-64/bin/mihomo/mihomo.exe \
  -f "/c/Users/Sun47/OneDrive/翻墙/Clash_bt.yaml"
```

The default `♻️自动选择` group uses url-test against `https://cp.cloudflare.com` and may select a node that doesn't handle BT traffic. Forcing the BT node can help with peer connectivity.

Since there is no `external-controller` API configured, you cannot switch proxy nodes at runtime — you must restart mihomo with a modified config.

## Python3 in git-bash Limitation

`python3` consistently exits with code 49 when:
- Piped from curl: `curl ... | python3 -c "..."` → exit 49
- Called with arguments: `python3 script.py arg` → exit 49
- Called after file write then read: `python3 script.py` → exit 49

**Workarounds:**
- Save curl output to file first, then read file with execute_code or read_file tool
- Use **PowerShell** for file text replacement:
  ```powershell
  powershell.exe -Command "(Get-Content path) -replace 'old','new' | Set-Content path"
  ```
- Use the `write_file` / `patch` / `execute_code` tools instead of python3 in terminal
- Read file contents with `read_file` tool rather than python3

## Pitfalls

1. **User preference: no questions asked when downloading**. When the user says "下载" or "下这个本子", they want immediate execution. Do NOT ask "下哪个版本?" or "要不要试这个?" — just pick the best option and execute. If the first attempt fails, silently try alternatives. Only stop to ask if EVERY option has been exhausted.

2. **Proxy nodes expire**: Many mihomo proxy nodes may be dead. Always test with `httpbin.org/ip` first. If 503, try a different node or skip proxy.

3. **0 seeders = dead torrent**: Check seed count before downloading. Use `s=seeders&o=desc` sort param.

4. **Port 6881 cleanup between runs**: Leftover aria2c zombie processes hold TCP/UDP port 6881, causing subsequent runs to fail silently with `CN:0`. Always check and clean:
   ```bash
   netstat -ano | grep 6881
   taskkill //F //PID <zombie_pid>
   ```

5. **Metadata stuck / CN:0**: If `0B/0B CN:0 SD:0 DL:0B` persists >60s, try:
   1. **Check for port conflicts** — zombie aria2c processes from previous runs occupy port 6881 (see pitfall #4).
   2. **Download .torrent file first** — avoid magnet metadata resolution entirely. Get the .torrent from sukebei via curl+proxy, then use it with aria2c.
   3. **Use HTTP trackers only without proxy** — start with `http://sukebei.tracker.wf:8888/announce` and no proxy. This got 22 connections in practice.
   4. **Use `--all-proxy` as last resort** — `--all-proxy` CAN work (got CN:24 in one test), but results are inconsistent because mihomo's `♻️自动选择` may change proxy nodes mid-session. If you try it, force the BT proxy node by modifying the config first (see §BT Proxy Nodes).

6. **GFW blocks BT data flow even when peers connect**: In China, the GFW performs deep packet inspection on BitTorrent protocol traffic. Even when aria2c shows `CN:22` (22 connections established), `DL` can stay at `0B` because the GFW throttles/resets BT data packets after TCP handshake. This is a fundamental limitation — if `CN>0` but `DL=0B` persists >2 minutes, BT connections are being GFW-blocked. Alternatives:
   - **Use Free Download Manager (FDM) as the proven fallback for large packs** — 琉璃神社 monthly collections (11-12GB) downloaded successfully via FDM when aria2c hit `DL:0B`. FDM is a GUI app: pass the magnet as a CLI arg with `terminal(background=true)` (foreground hangs on the GUI loop), then the user confirms the save path in the popup — the task does NOT auto-queue. See `references/liuli-monthly-collection.md` for the full workflow.
   - Use a proper TUN/VPN (not just HTTP/SOCKS proxy) so the ISP sees only encrypted tunnel traffic
   - Switch to a BT-specific proxy node (Hysteria2 with port hopping, see §BT Proxy Nodes)
   - Abandon BT and find a direct HTTP download or 115网盘 offline

7. **aria2c does NOT support SOCKS5 proxy**: Only supports HTTP/HTTPS/FTP proxy (`--all-proxy`, `--http-proxy`, `--https-proxy`). For full BT traffic through proxy, use mihomo in TUN mode or configure a BT-specific HTTP proxy node that handles CONNECT to arbitrary ports.

8. **Gzip encoding**: Always use `--compressed` flag with curl to get readable HTML from sukebei.

9. **Run in background**: Always use `terminal(background=true, notify_on_complete=true)` for downloads.

10. **`-d` vs `-f` for mihomo**: Use `-f` to specify config file path directly. `-d` is working directory (looks for `config.yaml`).

11. **Pipe to Python in git-bash**:
    `python3` in git-bash (MSYS2) often exits with code 49 when piped or invoked with arguments. Always save curl output to a file first, then read it with `read_file` or `execute_code`. See the **Python3 in git-bash Limitation** section above for workarounds.**

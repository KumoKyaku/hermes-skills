---
name: torrent-download
title: Torrent & Magnet Download
description: Download torrents/magnets via aria2c on Windows, with mihomo proxy for GFW-blocked trackers. JAV/doujinshi search workflow included.
version: 1.3.0
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
- **行为有三种，必须截图确认**（2026-08-09 与 2026-08-12 实测）：
  - FDM **已在运行** + 记住了上次保存路径 → **不弹窗**，任务直接进队列自动开始下载，保存路径**沿用上次路径**（可能是旧目录，不一定是用户期望的！实测落在 `E:\SystemCacheInfo\琉璃神社\2026年合集\`，而资源并非月合集）
  - FDM 未运行 + 有路径记忆 → 弹出"添加下载"对话框，但**任务仍会用记住的路径自动开始下载**（2026-08-12 实测：对话框开着期间，9:51 建目录、9:53 已预分配 6.4GB 文件开始写入）
  - FDM 未运行 + 无路径记忆 → 弹窗等用户确认路径
- **⚠️ 不要折腾 GUI 改保存路径**（2026-08-12 实测）：pyautogui 点击改路径的做法失败率极高——vision_analyze 给的对话框坐标是**推测值**不可靠、pyautogui 的 screenshot 因 pyscreeze 缺失不可用无法核对、FDM 随时可能自动开下导致改了也白改。**正确做法：接受 FDM 记住的路径让它下，下载完成后用 `mv` 把文件移到目标目录**（单部 JAV 落到月合集目录时尤其如此）
- **✅ 根治方法：直接改数据库的 `FixedDownloadPath`**（2026-09-06 实测）：FDM 记住的保存路径存在 `C:/Users/Sun47/AppData/Local/Softdeluxe/Free Download Manager/db.sqlite` 的 `Settings` 表 `FixedDownloadPath`（还有 `DefaultDownloadPath`、`pathByFileType` 表）。之前所有下载跑偏到 `E:/SystemCacheInfo/琉璃神社/2026年合集` 就是因为 `FixedDownloadPath` 被设成了那个目录！**修复流程**：① 备份 db.sqlite（`cp` 到 Temp）→ ② `Stop-Process -Name fdm` 关掉 FDM → ③ `UPDATE Settings SET Value='E:/SystemCacheInfo/Others' WHERE Name IN ('DefaultDownloadPath','FixedDownloadPath')` + `UPDATE pathByFileType SET path='E:/SystemCacheInfo/Others'`（pathByFileType 里可能有拼错路径的坏数据 `E:/下载/SystemCacheInfo/琉璃神社`）→ ④ background 重启 fdm.exe → ⑤ 查库确认值保持。**FDM 必须在关闭状态下改库**，运行中改会被覆盖。以后新下载默认落 `Others`，只有琉璃神社合集才需临时指到琉璃神社目录。
- 传完后**用 PowerShell 截图确认**任务已进队列、保存路径是否正确（screenshot.ps1 流程，见 windows-desktop-control 技能）
- 确认时留意：任务状态先"请求信息中"（解析磁力元数据，可能 30-60s），解析出文件名/大小后自动开下
- **后台等待完成**：用 `scripts/wait_fdm_download.sh "<目标目录>" [超时分钟=150]` 轮询 `.fdmdownload` 消失，配 `terminal(background=true, notify_on_complete=true)`，完成/超时自动通知

**aria2c 仅作为最后手段**（上面 FDM 不可用/用户要求时才用，见下方 Workflow）。

## Prerequisites

- **FDM**: `D:\Program Files\Softdeluxe\Free Download Manager\fdm.exe`（首选）
- **aria2c**（备选）: installed via `winget install aria2.aria2 --silent` → `C:\Users\<user>\AppData\Local\Microsoft\WinGet\Links\aria2c`
- **mihomo** (optional): for accessing GFW-blocked trackers/sites. Path: `OneDrive/翻墙/v2rayN-windows-64/bin/mihomo/mihomo.exe`, config: `OneDrive/翻墙/Clash_1777610321.yaml`
- **Default save directory**: `E:/SystemCacheInfo/Others/`
- **下载分类规则（用户 2026-08-22 显式要求"记住"）**: 只有**琉璃神社合集** → `E:\SystemCacheInfo\琉璃神社\`（20XX年合集/MM月合集 结构），**其他一切下载**（本子/JAV/小说/视频）→ `E:/SystemCacheInfo/Others/`。绝不把非合集资源塞进琉璃神社目录。

## Workflow

### 1. Search for content

For JAV codes or doujinshi, search on **sukebei.nyaa.si** (requires proxy). 域名备用：sukebei.nyaa.si 失效时用 **sukebei.nyaa.net**（2026-08-26 实测返回 200，同一套 HTML/磁力解析逻辑）:

```bash
curl -x http://127.0.0.1:7890 -s --compressed --max-time 20 \
  "https://sukebei.nyaa.si/?q=<URL_ENCODED_QUERY>&f=0&c=0_0&s=seeders&o=desc" \
  -H "User-Agent: Mozilla/5.0"
```

Extract magnet links from the HTML:
```python
import re, urllib.parse
magnets = re.findall(r'href="(magnet:\?xt=urn:btih:[a-zA-Z0-9]+[^"]*)"', html)
for m in magnets:
    dn = re.search(r'dn=([^&]+)', m)
    if dn:
        title = urllib.parse.unquote(dn.group(1))
```

⚠️ **sukebei HTML 解析细节**（2026-08-12 实测）：
- 按 `<tr>...</tr>` 分块时，**第一块是表头行**（含 `hdr-downloads`），实际结果从 `rows[1:]` 开始——直接 `rows[0]` 取会拿到空
- 磁力链接里的 `&` 在 HTML 里是 `&amp;` 转义，喂给 FDM/aria2c 前必须 `magnet.replace('&amp;', '&')`，否则 tracker 参数解析错误
- 种子数在 `s=seeders&o=desc` 排序下第一行就是最佳选择；`seeds` 列第一个数字是种子数，选 ≥10 的（0 种子 = 死种，见 Pitfall #3）
- 大体积资源（>5GB）可看标题里的 `[FHD]`/`[HD]`/`[H265 1080p]` 标签选版本

### 2. Start proxy (if needed)

⚠️ **必须用 Windows 原生路径（`C:\...`），不要用 MSYS 路径（`/c/...`）** —— MSYS 格式会让 mihomo 报 "Can't find config, create a initial config file"（2026-08-09 实测）。

```bash
terminal(background=true, command='"/c/Users/Sun47/OneDrive/翻墙/v2rayN-windows-64/bin/mihomo/mihomo.exe" -d "C:\\Users\\Sun47\\OneDrive\\翻墙" -f "C:\\Users\\Sun47\\OneDrive\\翻墙\\Clash_1777610321.yaml"')
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

### 5b. e-hentai for Chinese-translated doujinshi (汉化版首选)

⚠️ **sukebei 上搜不到 [中国翻訳] 版**（2026-08-22 实测：搜画师名「はいずり屋」只有日文原版 + 个别英/韩版）。用户要**汉化版**时，别在 sukebei 折腾，直接搜 e-hentai（需代理）：

```bash
curl -x http://127.0.0.1:7890 -s --compressed --max-time 25 \
  "https://e-hentai.org/?f_doujinshi=1&f_search=<URL_ENCODED_QUERY>&f_apply=Apply+Filter" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
```

- 画廊标题自带语言标签：`[Chinese] [白杨汉化组]` / `[English]` / `[Korean]` — 直接挑 `[Chinese]`
- 用画师名（日文/罗马音均可）搜，`<div class="glink">` 是标题，链接形如 `https://e-hentai.org/g/<id>/<token>/`
- **下载用 gallery-dl**（`python -m pip install gallery-dl`，hermes venv 已装 v1.32.9）：
  ```bash
  gallery-dl --proxy http://127.0.0.1:7890 -d "E:/SystemCacheInfo/Others/<画师>/" "https://e-hentai.org/g/<id>/<token>/"
  ```
- **无需登录/cookies** 即可下载（2026-08-22 实测 42 页 11MB 成功）
- 下载产物是 webp/jpg 单页图 + 超长画廊名目录（含 `[...]` 标签）— 交付前重命名成简洁中文名 + zip 打包
- **用户偏好（2026-08-22 显式要求"记住"）：解压后的图片要转成 PNG**。zip 解压后执行：
  ```bash
  cd "<解压目录>" && for f in *.webp; do ffmpeg -y -loglevel error -i "$f" "${f%.webp}.png"; done && rm -f *.webp
  ```
  webp→png 用 ffmpeg（hermes venv 的 PIL 不可用）；PNG 比 webp 大（42 页 11MB→72MB），是用户选择，照做不省
- **转封面/预览图**：hermes venv 的 PIL 不可用（`_imaging` ImportError），用 ffmpeg：`ffmpeg -y -loglevel error -i page.webp -frames:v 1 cover.jpg`
- 完整实测流程见 `references/ehentai-gallerydl-doujin.md`

### 6. Cleanup

**Always kill mihomo proxy after download to save monthly traffic (50GB cap):**
```bash
taskkill //F //IM mihomo.exe 2>&1 || powershell.exe -NoProfile -Command "Stop-Process -Name mihomo -Force"
```
⚠️ git-bash 里 `taskkill //F //IM` 可能报 `无效参数/选项 - '//F'`（MSYS 参数转换不一致，2026-08-09 实测）——PowerShell `Stop-Process` 是可靠兜底，杀掉后用 `tasklist | grep -i mihomo` 验证。

**Always deliver the file to the user when done.** Use `MEDIA:/path/to/file` to send images or files.

## Common Search Queries

| Type | Query Pattern |
|------|---------------|
| JAV by code | `KAWD-722` → `?q=KAWD-722` |
| Doujinshi by title/character | `学マス 同人誌` → `?q=%E5%AD%A6%E3%83%9E%E3%82%B9+%E5%90%8C%E4%BA%BA%E8%AA%8C` |
| Full game name | `学園アイドルマスター 同人誌` → more results than short name |
| Chinese mirror site search | Use 360搜索 (so.com) with Chinese terms, e.g. `角砂糖 学マス 结婚生活合同` |
| Chinese-translated doujinshi (汉化版) | e-hentai `?f_doujinshi=1&f_search=<画师名>` → 挑 `[Chinese]` 标签，gallery-dl 下载（见 §5b） |
| Anime/OVA by 中文译名 | 中文译名是本地翻译，sukebei 用**罗马音/日文原名**搜。先 web_search 中文名拿到日文原名+罗马音（TMDB 有双语条目，如 `我的初恋对象不可能是亲姐姐` → `Anehame` / アネハメ），再 `?q=anehame` 搜种。多集 OVA 通常每集一个种子，按种子数挑（如 SakuraCircle 01/02 各 33+/37+ 种） |

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

# Start mihomo with temp config（同样用 Windows 原生路径）
/c/Users/Sun47/OneDrive/翻墙/v2rayN-windows-64/bin/mihomo/mihomo.exe \
  -d "C:\Users\Sun47\OneDrive\翻墙" \
  -f "C:\Users\Sun47\OneDrive\翻墙\Clash_bt.yaml"
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
   - **Use Free Download Manager (FDM) as the proven fallback for large packs** — 琉璃神社 monthly collections (11-12GB) downloaded successfully via FDM when aria2c hit `DL:0B`. FDM is a GUI app: pass the magnet as a CLI arg with `terminal(background=true)` (foreground hangs on the GUI loop). ⚠️ 若 FDM 已在运行，任务会自动进队列下载、不弹窗、保存路径沿用上次（2026-08-09 实测）——传完后截图确认路径，必要时提醒用户改。见 `references/liuli-monthly-collection.md` for the full workflow.
   - Use a proper TUN/VPN (not just HTTP/SOCKS proxy) so the ISP sees only encrypted tunnel traffic
   - Switch to a BT-specific proxy node (Hysteria2 with port hopping, see §BT Proxy Nodes)
   - Abandon BT and find a direct HTTP download or 115网盘 offline

7. **aria2c does NOT support SOCKS5 proxy**: Only supports HTTP/HTTPS/FTP proxy (`--all-proxy`, `--http-proxy`, `--https-proxy`). For full BT traffic through proxy, use mihomo in TUN mode or configure a BT-specific HTTP proxy node that handles CONNECT to arbitrary ports.

8. **Gzip encoding**: Always use `--compressed` flag with curl to get readable HTML from sukebei.

9. **Run in background**: Always use `terminal(background=true, notify_on_complete=true)` for downloads.

10. **`-d` vs `-f` for mihomo**: Use `-f` to specify config file path directly. `-d` is working directory (looks for `config.yaml`). **路径格式必须用 Windows 原生（`C:\...`）**：git-bash 里传 MSYS 路径（`/c/...`）给 `-f`/`-d` 会报 `Can't find config, create a initial config file`，节点全失效。见 §2 的启动命令。⚠️ 补充（2026-09-05 实测）：同时给 `-d` 和 `-f` 时 `-f` 会被当作相对 `-d` 解析——从 mihomo 目录里 `-d . -f "/c/Users/.../Clash_1777610321.yaml"` 会报 `can't create file ...\mihomo\c\Users\...`（fatal）。最稳写法：先 `cd` 到配置所在目录（`OneDrive/翻墙`），只传 `-f "C:\Users\Sun47\OneDrive\翻墙\Clash_1777610321.yaml"`（绝对 Windows 路径），不传 `-d`。

11. **Pipe to Python in git-bash**:
    `python3` in git-bash (MSYS2) often exits with code 49 when piped or invoked with arguments. Always save curl output to a file first, then read it with `read_file` or `execute_code`. See the **Python3 in git-bash Limitation** section above for workarounds.**

12. **FDM 数据库有两个，别用错！**（2026-09-05 实测）：本机装了新旧两个 FDM——
    - **在用 = Softdeluxe 版 v6.34**（`D:\Program Files\Softdeluxe\Free Download Manager\fdm.exe`），数据库在 **`C:/Users/Sun47/AppData/Local/Softdeluxe/Free Download Manager/db.sqlite`**（表名 downloads，列：id/uuid/url/destinationType/destinationPath/title/creationTime/finishedTime/flags…）。查 FDM 状态/记住路径查这个！
    - 旧的 ORG 版（`D:\Program Files\FreeDownloadManager.ORG\...`）数据库在 `C:/Users/Sun47/AppData/Local/Free Download Manager/fdm.sqlite`，**2024-05 之后就不再写**（BrowserNativeHostPath 指向 ORG 目录、downloads 最新记录停在 2024-05-05、路径指向已不存在的 D:/下载）——别在这个库上浪费时间
    - Softdeluxe 库可直接读：`SELECT id, destinationPath, title, flags FROM downloads ORDER BY id DESC`。新任务在"请求信息中"阶段就落库（id 递增可见，但 destinationPath/title 为 NULL），解析出元数据后填充。flags≈546314847 为已完成态。月合集任务 destinationPath = 父目录 `E:/SystemCacheInfo/琉璃神社/2026年合集`（种子顶层 `2026年MM月合集` 会在其下自建），title = `2026年MM月合集`
    - 可靠监控法：① PowerShell 截图看 FDM 窗口的速度/进度/剩余时间；② 直接 `ls` 目标目录，下载中文件带 `.fdmdownload` 后缀（如 `xxx.mp4.fdmdownload`），完成后后缀消失、`find -name '*.fdmdownload' | wc -l` 归零即全部完成
    - FDM 界面显示的速度是瞬时值（会从 2MB/s 掉到 380KB/s 波动），看进度 % 和剩余时间更稳
    - ⚠️ 全屏截图可能拍不到 FDM 窗口（2026-08-26 实测：FDM 在后台被浏览器遮挡，CopyFromScreen 截到的是前台程序）。文件系统（`.fdmdownload` 出现 + `du -sh` 增长）才是主判据，截图仅补充；要看 FDM 界面先把它带到前台再截

13. **种子自带推广垃圾文件**（草榴/2048 社区系种子常见）：主视频之外会附带 10-18 个推广文件——`2048地址发布器PC版/手机版`、`2048QR二维码.png`、`1024草榴社區 t66y.com.txt`、`UU直播/台湾uu美少女直播` 宣传小视频（~23MB/个）、`最新国产日韩欧美新片合集发布.html` 等，全部落盘。下载完成后询问用户是否清理，只留主视频（本次实测：18 个文件里 17 个是推广垃圾，主视频 903MB）。
    - **繁体推广文件特征**（MUKC-094-C 实测 2026-08-22）：文件名带空格、繁体中文、宣传性质——`聚 合 全 網 H 直 播.html`、`社 區 最 新 情 報.mp4`、`台 妹 子 線 上 現 場 直 播 各 式 花 式 表 演.mp4`、`最 新 位 址 獲 取.txt`——直接删，只留正片。
    - **用户说「整理」= 目录整理标准**：① JAV 统一为 `番号/番号.mp4` 文件夹结构；② 根目录散文件收进同名文件夹（如 `IPZZ-003.mp4` → `IPZZ-003/`）；③ 清掉种子推广垃圾；④ 最终根目录 0 散文件。整理完给用户表格化汇总（每项 + 大小）。

14. **curl `-o` 写文件路径用 Windows 绝对路径**（2026-08-12 实测）：git-bash 里 `curl -o "$HOME/.hermes_tmp/x.html"` 会 exit 23（write error，MSYS 路径展开问题），改成 `curl -o "C:/Users/Sun47/.hermes_tmp/x.html"` 或 `/c/Users/Sun47/...` 绝对路径就正常。同理 mihomo 的 `-f`/`-d`（见 Pitfall #10）。⚠️ 补充（2026-08-26 实测）：sukebei 响应 `Content-Encoding: zstd`，**用对了 Windows 绝对路径但漏了 `--compressed` 同样 exit 23**——路径和 `--compressed` 两个条件都要满足才稳。

15. **FDM 下载完成判据 = `.fdmdownload` 消失 + `du -sh` 实际占用≈逻辑大小**（2026-08-26 补充：后缀消失≠完成！）：FDM 预分配全量文件（稀疏文件，`ls` 显示 5.37GB 但实数据只有 ~510MB），`ls -la` 的字节数毫无意义，必须看 `du -sh` 实际占用。**⚠️ `.fdmdownload` 后缀消失不一定是下载完成**——任务被停止/出错时 FDM 也会去掉后缀（实测：任务"已停止"时后缀消失，实际只下了 9%）。验证：① `du -sh` 实数据 vs 逻辑大小；② Python 读文件头/中/尾——头部 ftyp 正常但中尾部全 0 = 稀疏空洞 = 没下完。配合 `scripts/wait_fdm_download.sh` 轮询，脚本报完成后仍要 `du -sh` 验证实数据≈逻辑大小。详见 `references/fdm-partial-resume-and-gui.md`。

16. **磁力链接被聊天软件塞表情/文字垃圾**（QQ/飞书粘贴 magnet 常见，2026-08-22 实测）：用户发来的磁力形如 `magnet:?[微笑]xt=urn:btih:a3205[微笑]14ec7f...`——聊天客户端把 emoji 渲染成 `[微笑]` 文本插入链接中间，还会带 `查看图片` 等尾巴。**清理方法：只保留 `magnet:?xt=urn:btih:` + 40 位 hex 字符**，丢弃其余所有字符：
   ```python
   import re
   raw = "magnet:?[微笑]xt=urn:btih:a320514ec7fd2e4163799f[微笑]099507208cdd7fe375[微笑]查看图片"
   btih = re.sub(r'[^0-9a-fA-F]', '', raw.split('urn:btih:')[1])
   magnet = f"magnet:?xt=urn:btih:{btih}"   # 校验 len(btih) == 40
   ```
   ⚠️ BTIH 恒为 40 位 hex（SHA-1）；清理后长度≠40 说明链接本身残缺，先跟用户确认再下载。

17. **磁力卡"请求信息中"（FDM）→ 死种判定三板斧**（2026-08-22 实测）：
   FDM 任务长期停在"请求信息中"（解析不出元数据）时，不要干等，依次排查：
   1. **aria2c 探活**：`aria2c --bt-metadata-only=true --bt-save-metadata=true --bt-tracker="<http trackers>" <magnet>` 跑 60s——`CN:0` 持续 = 死种（无活源），直接放弃
   2. **btdig 查 hash 识别内容**：`curl -x http://127.0.0.1:7890 -sL "https://btdig.com/search?q=<40位hex>"`，能拿到种子文件名/大小，确认用户想要的到底是什么（本次实测：用户发的磁力实为 `kaori_xoxo private SNS myfans (1080).mp4` 78MB，跟 FDM 列表里 8月9日 已完成的同名"极品童颜巨乳百变福利姬"不是同一个东西）
   3. **查本地是否已下过**：`ls 下载目录 | grep 关键词`——FDM 列表里同名任务显示"已完成"= 旧档，别重复下
   死种结论直接告诉用户换源/忽略，别耗时间等。
   ⚠️ **反向情形（2026-09-05 实测）：FDM 卡"请求信息中" ≠ 死种**。07月合集磁力 FDM 卡了 10+ 分钟仍在"请求信息中"，但 aria2c 探活 ~90s 就拿到元数据（`[MEMORY][METADATA] Download complete`，CN:5）——种子有活源，纯粹是 FDM 解析慢/卡。**判定死种以 aria2c 探活为准**（aria2c 也 `CN:0` 持续 90s+ 才是死种），别因为 FDM 卡着就告诉用户死种。
   探活成功后别干等 FDM：用 `aria2c --show-files <saved>.torrent` 查看种子内容（顶层目录名/文件清单/总大小，秒级确认 hash 对应正确内容），然后可尝试把 aria2c 存出的 `<hash>.torrent` 直接喂 FDM（`fdm.exe 'C:/.../<hash>.torrent'`）跳过磁力解析——但若 FDM 里已有同 hash 磁力任务会弹"下载已存在"（见 Pitfall #20），需先删掉卡住的磁力任务再喂 .torrent。
   ⚠️ **删任务 + 重喂 .torrent 全流程已完整验证**（2026-09-05，07月合集 13.5GiB 成功）：
   1. **删除卡住的磁力任务**：FDM 窗口激活（pygetwindow）→ 键盘 Down 选中目标行（详情面板确认选中对）→ Delete → 弹确认框 Esc/Enter 关掉。**验证删除**：查 Softdeluxe 库 `SELECT id FROM downloads ORDER BY id DESC LIMIT 1`，该 id 消失即删除成功（本机验证 id=102 消失；删除的是任务不删文件，磁力还没下数据所以无损失）
   2. **喂 .torrent**：`terminal(background=true, ... ./fdm.exe 'C:/Users/Sun47/AppData/Local/Temp/<hash>.torrent')`（FDM 已在运行时不弹窗，任务直接进队列）
   3. **✅ .torrent 直喂 vs 磁力的关键优势（实测）**：任务**创建即带齐 destinationPath + title**（查库秒见 `2026年07月合集` / `E:/SystemCacheInfo/琉璃神社/2026年合集`），**完全没有"请求信息中"阶段**，立即开始下载。磁力要等 30-60s+ 解析、还可能卡死；.torrent 直喂零等待。以后凡是有 .torrent 文件可用的场景（aria2c 探活存出的、sukebei 下载的），**优先喂 .torrent 而不是磁力**！
   4. 下载完成验证用**字节求和法**（比 du -sh 更精确）：`python` os.walk 遍历目标目录所有文件字节求和，与 `aria2c --show-files` 的 Total Length 比对，零误差 = 100% 完整（07月实测 14,493,322,778 == 14,493,322,778）

18. **FDM 低速模式（乌龟图标）把速度锁到 KB/s 级**（2026-08-26 实测）：任务显示"剩余 X天"、速度个位数 KB/s 时，先查 FDM 工具栏"低速模式"（乌龟图标，添加/开始/暂停/停止/删除之后第 6 个左右）是否被激活（高亮）。激活时全局限速，点掉即恢复。⚠️ 工具栏按钮坐标点击易点偏（实测按估算坐标点中任务列表选中了别的任务）——点击后必须截图验证状态变化。定位按钮用 `scripts/png_pixel_analyze.py` 分析截图彩色像素簇（PIL/numpy 在 hermes venv 都不可用时的纯 stdlib 方案，numpy 报 cp311/cp313 不匹配）。

19. **用户手动改 `.fdmdownload` 后缀会弄坏断点续传**（2026-08-26 实测）：文件没下完时把 `.fdmdownload` 改名 `.mp4` → FDM 任务变"文件丢失"（找不到临时文件），且稀疏文件（中后部空洞）无法播放。恢复：`mv` 改回 `.fdmdownload` → `powershell.exe -NoProfile -Command "Stop-Process -Name fdm -Force"`（git-bash taskkill //F 报无效参数，同 mihomo）杀 FDM → background 重启 fdm.exe → 任务恢复"下载中"并识别断点（实测 9% 进度保留）。教训：下载完成前绝不改后缀；已改则改回 + 重启 FDM 可救。

20. **FDM 运行中重复添加同一磁力 → 弹"下载已存在"对话框**（2026-08-26 实测）：技能正文"FDM 已在运行→不弹窗直接进队列"仅适用于**新**磁力；同磁力已有任务（哪怕已停止）时会弹"下载已存在"框（显示链接/路径/大小/添加时间），按 Enter 确认默认按钮即可。若任务处于"文件丢失"状态，弹框确认后仍不会下——先按 #19 恢复再续传。

21. **fdm.exe 一次只接收一个 .torrent**（2026-09-06 实测）：`./fdm.exe a.torrent b.torrent` 传多个参数时**只有第一个进队列**，其余静默丢失——必须每个 .torrent **单独调一次** fdm.exe（background 启动，间隔几秒等落库）。多集 OVA/番剧每集一个种子的场景（如 Anehame 01/02）尤其要逐集喂，喂完查库 `SELECT id, url FROM downloads ORDER BY id DESC LIMIT 2` 确认每个 .torrent 都落了任务。

22. **git-bash 给原生工具传含日文/中文的绝对路径 → "Illegal byte sequence"**（2026-09-06 实测）：目标目录是 `E:/SystemCacheInfo/Others/アネハメ俺の初恋が実姉なわけがない/...` 这类日文名目录时，ffprobe/ffmpeg 接绝对路径直接报 `Illegal byte sequence` 拒绝打开（MSYS 参数编码问题，与 Pitfall #10/#14 同族）。**解法：`cd` 进目录后只传相对文件名**（`./file.mkv`）。下载完验证视频用：
   ```bash
   cd "<目标目录>" && for f in *.mkv; do echo "== $f =="; ffprobe -v error -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 "./$f"; done
   ```
   `codec_name=ass` 出现 = 内嵌软字幕轨（SakuraCircle 这类英字版 mkv 是 h264+AAC+ASS，播放器可开关字幕）；交付前可 `ffmpeg -ss 00:01:00 -i ./file.mkv -frames:v 1 preview.jpg` 截帧 + vision 确认画面正常。

---
name: windows-content-download
description: Download files via BitTorrent/magnet, HTTP, and other methods on Windows — aria2c setup, proxy integration for GFW-blocked trackers, and default download location conventions.
version: 1.0.0
author: 阿库娅 💧
tags: [download, bittorrent, magnet, aria2c, jav, windows]
related_skills: [network-proxy, windows-software-install]
---

# Windows Content Download

Download files (torrents, magnets, direct HTTP) on a Windows system behind the GFW.

## ⚠️ 工具选择：FDM 优先

**用户明确要求：FDM 优先，不用 aria2c。**（2026-08 确认）

- **BT/磁力下载** → 一律用 **Free Download Manager**（`D:\Program Files\Softdeluxe\Free Download Manager\fdm.exe`，GUI，background 启动），详细流程见 `torrent-download` 技能
- aria2c 仅作最后手段，且失败会留 0 字节嵌套空壳 + `.aria2` 残留，下载后要清理验证
- 本技能与 `torrent-download` 内容有重叠；BT/磁力细节以 `torrent-download` 为准

## Default Download Location

All downloaded content goes to `E:/SystemCacheInfo/Others/`.

## aria2c — BitTorrent & Magnet Downloads

### Installation

```bash
winget install aria2.aria2 --silent
```

Installs `aria2c` to `%LOCALAPPDATA%\Microsoft\WinGet\Links\aria2c` (on PATH after install).

### Basic Magnet Download

```bash
cd /e/SystemCacheInfo/Others
aria2c --seed-time=0 "magnet:?xt=urn:btih:HASH..."
```

`--seed-time=0` stops seeding immediately after download completes (user's preference — don't waste bandwidth/disk).

### With Proxy (trackers/peers behind GFW)

JAV torrents from sukebei.nyaa.si often have trackers behind the GFW. Use the mihomo proxy:

```bash
cd /e/SystemCacheInfo/Others
aria2c --seed-time=0 --all-proxy="http://127.0.0.1:7890" \
  --bt-tracker="udp://tracker.opentrackr.org:1337/announce,udp://tracker.openbittorrent.com:6969/announce" \
  --max-connection-per-server=16 --split=16 --bt-max-peers=100 \
  "magnet:?xt=urn:btih:HASH..."
```

**Important**: Start mihomo proxy first (see `network-proxy` skill). Kill it after the BT engine has resolved the metadata and connected to peers — aria2c can continue downloading without the proxy once peer connections are established.

### Recommended aria2c Flags

| Flag | Value | Reason |
|------|-------|--------|
| `--seed-time=0` | — | Stop seeding immediately |
| `--all-proxy` | `http://127.0.0.1:7890` | If behind GFW |
| `--bt-tracker` | comma-separated list | Multiple trackers for better peer discovery |
| `--bt-max-peers` | 100 | Good balance for Chinese network |
| `--max-connection-per-server` | 16 | Speed up downloads |
| `--split` | 16 | Parallel connections |

## Finding JAV Magnet Links

### Primary Source: sukebei.nyaa.si (requires proxy)

1. Start mihomo proxy
2. Query via Python requests:
   ```python
   import requests, re
   proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
   r = requests.get(f'https://sukebei.nyaa.si/?q={CODE}&f=0&c=0_0&s=seeders&o=desc',
                     headers=headers, proxies=proxies, timeout=15)
   magnets = re.findall(r'href="(magnet:\?xt=urn:btih:[^"]+)"', r.text)
   ```

3. Sort by seeders (`s=seeders&o=desc`) for the best source.

### Alternative Sources (also require proxy)

- **javdb.com**: Returns 403 even through current proxy — unreliable
- **javbus.com**: GFW-blocked
- **javlibrary.com**: GFW-blocked

### Version Selection Heuristics

When multiple versions exist for the same JAV code, prefer:
1. **去码版 / Reducing Mosaic** (~1.5-2 GiB) — best balance of quality and size
2. **H265 1080p** (~2-3 GiB) — modern codec, smaller than H264
3. 其他版本: larger files (7-8 GiB) for original quality, only if user requests

## Novel Download (Direct vs Scraping)

**User preference**: Always try direct download links first. Only scrape as last resort.

When scraping from sites like 22biqu.com is the only option:
1. First collect ALL chapter links from all pages
2. Download chapters in order with retry logic (3 attempts per chapter)
3. Verify completeness by comparing chapter count against expected total
4. 小说下载完整流程见 `chinese-novel-download` 技能（22biqu 站点细节、缩水章节警告、百度网盘流程都在那里）

## Verification

After any download:
- Check file exists at target path
- Check file size is non-zero and reasonable
- For torrents, confirm metadata was fetched (not just `.aria2` temp file)

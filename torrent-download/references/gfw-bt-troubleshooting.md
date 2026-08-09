# GFW BitTorrent Troubleshooting — Session Notes

Session date: 2026-07-17
Torrent: `IPZZ-276` (6.2GB, 22 seeders on sukebei)
Environment: Windows 10, Guangzhou, China (GFW active)

## Problem

From China, you cannot download BitTorrent through a regular HTTP/SOCKS5 proxy. The GFW blocks:
- UDP tracker announces (except some HTTP trackers)
- DHT bootstrap packets
- BitTorrent peer-to-peer data packets (DPI-based)

## What Worked (Partially)

**Direct connection with HTTP trackers (no proxy)**
- `aria2c` connected to 22 peers immediately when run WITHOUT proxy
- But DL stayed at 0B — GFW blocked the actual data flow after TCP handshake
- CN:22, SD:0, DL:0B → peer connections established, no data flowing

**`--all-proxy` with HTTP proxy (inconsistent)**
- First attempt: CN:24, SD:1, completed metadata download (62KiB)
- Error was "File exists" not network-related
- Subsequent attempts: CN:0 (port conflict from zombie processes was the real cause)
- After port cleanup: still CN:0 (proxy node selection changed)

## Debugging Steps Taken

### Port cleanup (MANDATORY between runs)
```bash
# Check port 6881
netstat -ano | grep 6881
# Kill zombies
taskkill //F //PID <PID>
```

### Proxy node selection
The mihomo config (`Clash_1777610321.yaml`) uses `♻️自动选择` (url-test) which picks the fastest node to `cp.cloudflare.com`. This may pick a non-BT-friendly node. Forcing the BT node (`🇺🇦 bt下载-乌克兰h-0.5倍率`) requires config modification + restart.

### Config modification
PowerShell (NOT python3 in git-bash, which exits with code 49):
```powershell
powershell.exe -Command "(Get-Content 'Clash_1777610321.yaml') -replace '♻️自动选择', '🇺🇦 bt下载-乌克兰h-0.5倍率' | Set-Content 'Clash_bt.yaml'"
```

### aria2c proxy limitation
- `--all-proxy=http://127.0.0.1:7890` — HTTP CONNECT only, unreliable for BT
- NO `--socks-proxy` option exists
- Only `--all-proxy`, `--http-proxy`, `--https-proxy`, `--ftp-proxy` are supported

### Direct download search results
- javlibrary.com → blocked by Cloudflare
- javbus.com → age verification page
- so.com search → times out
- bing search → returns Chinese-internal results only (no direct download links)

## Recommendations for Future Attempts

1. **TUN mode** — Configure mihomo with `tun:` section for full VPN-like transparent proxy
2. **115网盘离线** — Upload magnet to 115, download from there (best China option)
3. **BT-specific proxy node** — Modify mihomo config to force `🇺🇦 bt下载-乌克兰h-0.5倍率` (Hysteria2 with port hopping)
4. **qBittorrent** — Try a different client that may handle GFW throttling differently

# e-hentai + gallery-dl 下载汉化版同人志

2026-08-22 实测：`[はいずり屋 (ずり太)] パンストフェチでもいいですか… [中国翻訳]`（白杨汉化组，42 页 11MB）。

## 适用场景

用户要**中文翻译版**（标题带 `[中国翻訳]` / 汉化组名）同人志。sukebei 只会有日文原版，e-hentai 是汉化版的主来源。

## 搜索

```bash
curl -x http://127.0.0.1:7890 -s --compressed --max-time 25 \
  "https://e-hentai.org/?f_doujinshi=1&f_search=%E3%81%AF%E3%81%84%E3%81%9A%E3%82%8A%E5%B1%8B&f_apply=Apply+Filter" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
```

解析要点（execute_code / Python 正则）：
- 画廊标题：`<div class="glink">(.*?)</div>`（含语言标签 `[Chinese] [白杨汉化组]`）
- 画廊链接：`href="(https://e-hentai\.org/g/[^"]+)"`
- 一个画师名可能出多个语言版本（英/韩/中），按标题里的 `[Chinese]` 挑

## gallery-dl 安装

```bash
python -m pip install gallery-dl
gallery-dl --version   # 实测 1.32.9
```

`python` 是 hermes venv 的 Python 3.11.15（git-bash 里 `python3` 不可用，用 `python`）。

## 下载

```bash
gallery-dl --proxy http://127.0.0.1:7890 \
  -d "E:/SystemCacheInfo/Others/<画师名>/" \
  "https://e-hentai.org/g/3422946/4cf67e5a87/"
```

- **无需登录、无需 cookies**，代理直下即可（本会话 e-hentai 没有验证码拦截）
- 输出：`<画师名>/exhentai/<画廊完整名>/<id>_00NN_*.webp|.jpg`
- 画廊完整名含 `[` `]` 等特殊字符和空格，后续 shell 操作注意引用

## 交付整理

1. 重命名目录为简洁中文名（去掉哈希前缀和 `[...]` 标签）：
   ```bash
   mv "exhentai/3422946 [Haizuriya ...] [Chinese] [白杨汉化组]" "パンストフェチでもいいですか_中国翻訳_白杨汉化组"
   ```
   ⚠️ 旧 `exhentai/` 空目录若报 `Device or resource busy`，先 `find exhentai -type f` 确认已空，稍等重试 `rm -rf`。
2. zip 打包（按页序重命名，PIL 不可用但 zipfile 是 stdlib）：
   ```bash
   python -c "
   import zipfile, os
   files = sorted(os.listdir(src))
   with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
       for i, f in enumerate(files, 1):
           ext = os.path.splitext(f)[1]
           z.write(os.path.join(src, f), f'{i:03d}{ext}')
   "
   ```
3. 封面转 jpg 发预览（hermes venv PIL 报 `ImportError: cannot import name '_imaging'` → 用 ffmpeg）：
   ```bash
   ffmpeg -y -loglevel error -i "3422946_0001_*.webp" -frames:v 1 "C:/Users/Sun47/.hermes_tmp/cover.jpg"
   ```
4. 发送：`MEDIA:封面.jpg` + `MEDIA:xxx.zip`（飞书/QQ 都吃 MEDIA 协议）

## 用户偏好：解压后图片转 PNG（2026-08-22 显式要求"记住"）

用户要求 zip 解压后的图片是 PNG 而非 webp。webp→png 用 ffmpeg 批量转（hermes venv 的 PIL 不可用），转完删 webp：

```bash
cd "<解压目录>" && for f in *.webp; do ffmpeg -y -loglevel error -i "$f" "${f%.webp}.png"; done && rm -f *.webp
```

注意：PNG 体积显著大于 webp（本次 42 页 11MB → 72MB），但这是用户偏好，照做不省。

## 死种/磁力异常排查（2026-08-22 实测）

- 用户从 QQ/飞书粘贴的磁力可能被聊天软件塞入 `[微笑]` 等表情文本和 `查看图片` 尾巴——**只保留 `magnet:?xt=urn:btih:` + 40 位 hex**，`re.sub(r'[^0-9a-fA-F]', '', ...)` 清理，校验 `len==40`
- FDM 任务卡"请求信息中"（解析不出元数据）→ aria2c `--bt-metadata-only` 探活，`CN:0` 60s = 死种
- btdig 查 hash 识别真实内容：`curl -x http://127.0.0.1:7890 -sL "https://btdig.com/search?q=<40hex>"`——确认用户要的到底是什么，避免跟本地已下过的同名旧档混淆
- 查本地是否已下过：`ls 下载目录 | grep 关键词`，FDM 列表同名任务"已完成" = 旧档

## 清理

下载完杀掉 mihomo 省流量：`powershell.exe -NoProfile -Command "Stop-Process -Name mihomo -Force"`（git-bash 的 `taskkill //F //IM` 可能报参数错，PowerShell 是可靠兜底）。

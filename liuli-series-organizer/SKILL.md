---
name: liuli-series-organizer
description: 琉璃神社视频库按系列整理工具 — 全量扫描、AI语义合并、硬链接归类、去重、海报简评匹配
category: media
---

# 琉璃神社 按系列整理工具

## 适用场景
琉璃神社目录结构 `YYYY年合集/YYYY年MM月合集/{CHS,CHT,RAW,XX月海报}/`，
需要用硬链接按视频系列重新组织目录，方便按系列浏览。

**基础路径：** `E:\SystemCacheInfo\琉璃神社\`
**输出路径：** `E:\SystemCacheInfo\琉璃神社_按系列\`

## 核心原则：先全量扫，再AI合并，再匹配媒体，再创建目录

不要把处理和扫描混在一起。正确流程：

```
Phase 1:  全量扫描视频 → 得到原始系列清单
Phase 1b: AI语义合并  → 合并同一语义的不同命名
Phase 2:  匹配媒体    → 海报/封面/简评匹配到系列
Phase 3:  创建目录    → 硬链接输出
```

## Phase 1 — 全量扫描

扫描所有视频子目录（`720P/`、`720P Hi10P/`、`HEVC/`、`Ma10p/`、`Raw[1080P]/`、`CHS/`、`CHT/`、`BIG5/`、`GB/`、`RAW/` 等），
用 9 种策略逐步尝试解析文件名。详见 `references/regex-patterns.md`。

### 系列名归一化步骤

```python
title_clean = EPISODE_PAT.sub('', rest).strip()    # 去话数后缀（＃1, 第1話, Vol.1 等）
norm = title_clean.strip("～").strip()              # 去首尾 ～（防止末尾残留 ～ 产生空段）
norm = re.sub(r'\s*\[[^\]]*\]\s*$', '', norm)       # 去末尾 [metadata]
norm = re.sub(r'^OVA[　\s]*', '', norm)              # 去 OVA 前缀
norm = re.sub(r'[　\s]*THE\s+ANIMATION\s*$', '', norm)  # 去末尾 THE ANIMATION
norm = norm.replace('!', '！').replace('?', '？')     # 全角标点归一（!? → ！？）
norm = re.sub(r'\s+[A-Z_0-9]+$', '', norm)            # 去末尾大写/编号残留

# ～ 拆分提取基础系列名
parts = norm.split("～")
if len(parts) >= 3:  norm_series = "～".join(parts[:2])    # 牝教師4～穢された教壇
elif len(parts) == 2: norm_series = parts[0]               # L'amour fou de l'automate
else: norm_series = norm
```

### 话数提取（ep_num）

```python
# 优先：＃1, 第1話, Vol.1, 前編, 後編 等数字标识
# 无数字时：用 ～ 后的描述部分作为 episode 标识
if len(parts) >= 3: ep_num = "～".join(parts[2:])[:30]
elif len(parts) == 2: ep_num = parts[1][:30]
else: ep_num = "full"
```

## Phase 1b — AI语义合并（关键！不要用正则前缀匹配合并）

**原则：** 不要用 `_longest_common_prefix` 之类的前缀匹配合并。这会把 `[720P]` 等错误条目
合并到一起。正确做法是分析全量系列名清单，手动编写 MERGE_MAP。

详见 `references/ai-merge-patterns.md`。

### 必须的清理步骤

在应用 MERGE_MAP 前，先清除 studio 是分辨率/编码标识的错误条目：

```python
for sk in list(data.keys()):
    studio = sk.split("]", 1)[0] + "]" if "]" in sk else sk
    sname = studio.strip("[]")
    # 可疑：含数字的短名称、BIG5/BIB5/RAW/HEVC 等编码标识
    if (re.search(r'\d', sname) and len(sname) <= 8 ...
```

## Phase 2 — 媒体匹配

扫描 `XX月海报/`、`封面/`、`前作/` 中的图片，匹配到对应系列。

### 匹配策略（三级）

```python
# 一级：精确匹配
if t == clean: return sk

# 二级：子串匹配（推荐，比字符交集更可靠）
if len(t) >= 3 and (t in clean or clean in t):
    return sk  # 取最长匹配

# 三级：字符交集（备选）
score = len(set(t) & set(clean))
if score >= 4: return sk
```

**注意：** 字符交集评分阈值 4 会漏掉短标题（如 `ママ喝っ` 只有 3 个不重复字）。
子串匹配先试，失败再降级。

### 简评匹配
- 解析 `*年*月里番简评.txt`，按 `《作品名》` 分割
- 匹配作品名到系列的归一化标题

## Phase 3 — 创建目录

### 目录结构

```
琉璃神社_按系列/
  [Studio]Series Title/
    CHS/  → .chs.mp4 硬链接
    CHT/  → .cht.mp4 硬链接
    RAW/  → .mkv 硬链接
    poster.png        ← 海报直接放根目录！
    cover.jpg         ← 封面直接放根目录！
    简评.txt          ← 简评直接放根目录！
```

### 规则
- **海报/封面不放子文件夹** — 直接放系列根目录，点进去就能看到
- **单集作品跳过**（只有 1 个话数编号的系列）
- **硬链接去重** — 同 `(ep_num, lang)` 只保留第一个文件
- **前作文件扫描时 `dedup_check=True`** — 跳过已有 `(ep_num, lang)` 组合
- **不删除任何原始文件**

## 只看简体：CHT（繁体）一律不保留

**用户明确要求（2026-10）：不看繁体版，以后下载也不要繁体。** 库里视频只留 `CHS/` 和 `RAW/`。

- 清理脚本：`scripts/purge_cht.py`（默认 dry-run，加 `--delete` 才真删）
- 关键：CHT 在「原始合集」和「按系列」两处都有硬链接，**只删一处不释放空间**，必须两棵树全扫全删，脚本按 `(st_dev, st_ino)` 去重算真实释放量
- 2026-10-17 实测：655 个 CHT / 422 个独立 inode / 释放 **152.25 GiB**（E 盘剩余 69→221 GB）
- ⚠️ **删前先查孤儿**：少数作品只有 CHT 没有 CHS。脚本以「月合集/系列目录」为单位递归比对 base_key，孤儿自动保留。当时剩 5 个（図書室ノ彼女、Knight of Erin 1st tale、くノ一○○伝 紫陽花 第二話、アオハルスナッチ2）
- 删完顺手清理变空的 `CHT/`、`BIG5/` 目录（当时清掉 124 个）
- 下载时就排除更省事：见 `torrent-download/references/liuli-monthly-collection.md` 的 `--select-file` 用法（省约 1/3 体积和带宽）

## 执行脚本

- 主脚本：`E:\SystemCacheInfo\琉璃神社\execute_series_v4.py`
- 直接运行：`cd E:\SystemCacheInfo\琉璃神社 && python execute_series_v4.py`
- 资源文件：`E:\SystemCacheInfo\琉璃神社\scripts\` 下的 v1-v3 是历史版本
- 改脚本前备份：`shutil.copy2(p, p + ".bak_before_xxx")`
- 跑之前可 `importlib.util.spec_from_file_location` 导入，干跑 `scan_all_videos()` + `apply_ai_merges()` 验证多集数，再正式执行
- 增量安全：脚本只 `mkdir` + `os.link`（目标已存在则跳过），不动原始文件，可反复重跑

## 已知陷阱与修复

### ⚠️ 2026年9月起的新命名格式（连写，无方括号）
**现象：** 整个 09 月合集的视频全部解析失败，既不进系列目录也不进单集清单。
**格式：** `YYMMDD + Studio + Title_第N話_副标题[_chs|_cht].ext`，例如
- `260925魔人NTR騎士_第1話_幼馴染は女騎士_魔術に墜ちる巨乳教官.mkv`
- `260904メリー・ジェーン小女ラムネ_第8話_リトルラバーズ_chs.mp4`
- `260911Queen_Bee村又さんの愛情_上巻井雲くす.mkv`（studio 自身含下划线）

**修复：** 加策略 J — 先剥离尾部 `_chs/_cht`，再用已知 studio 列表**按长度降序**做前缀匹配（Queen_Bee 必须先于 Queen 匹配），剩余部分把 `_` 全部换成空格后交给 `_make_info`。

### ⚠️ `_extract_ep` 无捕获组 → 所有 上巻/下巻/前編/後編 都返回 unknown
**现象：** 同一系列的上巻+下巻、前編+後編 被当成同一话，去重时只保留一个文件（`dedup=f"{ep}_{lang}"`），整个系列退化成单集被跳过。典型：ピュアホリック、寝取られた爆乳妻たち、村又さんの秘密。
**根因：** 正则分支 `|[前中後上中下][編巻話編]|` 没有捕获组，匹配成功但 `groups()` 全为 None → `parts` 为空 → 返回 `"unknown"`。
**修复：** 改成 `|([前中後上中下][編巻話編])|`。另加 `第?(\d+)時限目` 规则（优先于主正则），否则性指導員 1時限目/2時限目 也会撞车。

### ⚠️ 多话系列分散成 N 个 series_key（必须补 MERGE_MAP）
**现象：** `○○交配 第一話 優等生の彼女は…`、`小女ラムネ 第5話 …` 这类「基础名 + 话号 + 副标题」的作品，每话都生成独立 series_key，各自只有 1 集 → 全部当单集跳过，永远建不出系列目录。
**修复：** 在 MERGE_MAP 里逐条把 `[Studio]基础名 第N話 副标题` 映射到 `[Studio]基础名`。新增月份后先跑 `dump_keys` 式脚本 grep 关键词，确认所有分散 key 再写映射。合并后 ○○交配 从 0 个目录变成 8 话，小女ラムネ 5/6/7/8 话合并。

### ⚠️ 续作不能并进本篇
`寝取られた爆乳妻たち2 前編` 要映射到 `[Queen Bee]寝取られた爆乳妻たち2`，不能并进 `寝取られた爆乳妻たち`，否则 `上/下` 话号撞车。

### ⚠️ patch 工具在 E 盘可能 420s 超时
对本目录的 .txt/.py 做 patch 前端工具曾连续超时。改用写 Python 脚本 + `io.open(..., newline='')` 读写（保留 CRLF），比 patch 工具可靠。

### ⚠️ 正则陷阱：贪心 `.+` 吞扩展名
**现象：** `[nur]L'amour...chs.mp4` → `.+` 吞掉 `.chs`，让 `\.mp4$` 匹配
**根因：** 贪心 `(.+)` 回溯到 `.mp4` 就停，不继续检查 `chs.mp4`
**修复：** 用非贪心 `(.+?)` → `(.+?)\.(chs\.mp4|cht\.mp4|mkv|mp4)$`

### ⚠️ 繁简陷阱：`組` vs `组`
**现象：** 正则 `\[桜都字幕組?\]` 不匹配 `[桜都字幕组]`
**根因：** `組` (U+7D44) 和 `组` (U+7EC4) 不同 Unicode
**修复：** 用 `[組组]?` 同时匹配繁简

### ⚠️ 标点陷阱：`!?` vs `！？`
**现象：** 同一系列因半角全角标点被分开
**修复：** 归一化时 `replace('!', '！').replace('?', '？')`

### ⚠️ 分辨率被当 Studio
**现象：** `[720P][鈴木みら乃]` → PAT_A 把 `720P` 当 studio
**根因：** 格式 `[桜都字幕组][720P][YYMMDD][Studio]` 日期在分辨率后
**修复：** 加 C2 策略处理这种格式

### ⚠️ ～ 末尾残留
**现象：** `～微かな息吹～` split 产生 3 段（含空串），触发 3+ 合并
**修复：** `norm.strip("～")` 先去掉首尾 ～

### ⚠️ 图片匹配不到
**现象：** `ママ喝っ`（6 字）匹配不到海报，字符交集得分仅 3
**根因：** 短标题的独特字符数不足阈值 4
**修复：** 用子串匹配 `(t in clean)` 优先于字符交集评分

### ⚠️ 错误条目抢匹配
**现象：** `[BIB5][ばにぃうぉ～か` 比 `催眠性指導`（6 字）更长，子串匹配时优先
**修复：** 在语义合并阶段先清除所有 `[分辨率/编码]` 格式的错误 studio 条目

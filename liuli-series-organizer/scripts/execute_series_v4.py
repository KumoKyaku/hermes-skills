#!/usr/bin/env python3
"""
Phase 4: 全量扫描 → 智能归类 → 媒体匹配 → 目录创建
"""
import os, re, json, hashlib
from collections import defaultdict
from pathlib import Path

BASE = Path(r"E:\SystemCacheInfo\琉璃神社")
OUTPUT = Path(r"E:\SystemCacheInfo\琉璃神社_按系列")

# ── 话数/章节后缀正则 ──
EPISODE_PAT = re.compile(
    r'(?:[　\s]*(?:＃\d+|第[一二三四五六七八九十\d]+[話巻話]|'
    r'[前中後上中下][編巻話編]|'
    r'[一二三四五六七八九十]+[話巻日目]|'
    r'Vol\.?\d*\.?\d*|Episode\s*\d+|'
    r'[\（\(][^)）]*[\）\)]?))*$'
)

# ── 所有文件名解析策略 ──
def parse_video_filename(name: str, subdir: str = "") -> dict:
    """尝试所有策略解析视频文件名，返回 {studio, title_clean, ep_num, lang} 或 None"""
    name = name.strip()
    
    # 策略 A: 标准 [YYMMDD][Studio]Title.ext (用非贪心 +? 防止吞扩展名)
    m = re.match(r'\[(\d{6})\]\[([^\]]+)\](.+?)\.(chs\.mp4|cht\.mp4|mkv|mp4)$', name)
    if m:
        studio = m.group(2).strip()
        rest = m.group(3).strip()
        ext = m.group(4)
        lang = "CHS" if ext == "chs.mp4" else "CHT" if ext == "cht.mp4" else _lang_from_dir(subdir)
        return _make_info(studio, rest, lang)
    
    # 策略 B: [桜都字幕组][YYMMDD][res][BIG5/GB][Studio]Title.ext
    m = re.match(r'\[桜都字幕[組组]?\]\[\d{6}\]\[[^\]]+\]\[(BIG5|GB)\]\[([^\]]+)\](.+)\.(mp4|mkv)$', name)
    if m:
        lang = "CHT" if m.group(1) == "BIG5" else "CHS"
        return _make_info(m.group(2).strip(), m.group(3).strip(), lang)
    
    # 策略 C: [桜都字幕组][YYMMDD][res+BIG5/GB][Studio]Title.ext
    m = re.match(r'\[桜都字幕[組组]?\]\[\d{6}\]\[[^\]]+\s(BIG5|GB)\]\[([^\]]+)\](.+)\.(mp4|mkv)$', name)
    if m:
        lang = "CHT" if m.group(1) == "BIG5" else "CHS"
        return _make_info(m.group(2).strip(), m.group(3).strip(), lang)
    
    # 策略 C2: [桜都字幕组][res][YYMMDD][Studio]Title.ext (日期在分辨率后)
    m = re.match(r'\[桜都字幕[組组]?\]\[[^\]]+\]\[(\d{6})\]\[([^\]]+)\](.+)\.(mp4|mkv)$', name)
    if m:
        return _make_info(m.group(2).strip(), m.group(3).strip(), _lang_from_dir(subdir))
    
    # 策略 D: [桜都字幕组][YYMMDD][res][Studio]Title.ext
    m = re.match(r'\[桜都字幕[組组]?\]\[\d{6}\]\[[^\]]+\]\[([^\]]+)\](.+)\.(mp4|mkv)$', name)
    if m:
        return _make_info(m.group(1).strip(), m.group(2).strip(), _lang_from_dir(subdir))
    
    # 策略 E: [桜都字幕组][YYMMDD][Studio]Title.ext (无分辨率括号)
    m = re.match(r'\[桜都字幕[組组]?\]\[\d{6}\]\[([^\]]+)\]\s*(.+?)\.(chs\.mp4|cht\.mp4|mkv|mp4)$', name)
    if m:
        ext = m.group(3)
        lang = "CHS" if ext == "chs.mp4" else "CHT" if ext == "cht.mp4" else _lang_from_dir(subdir)
        return _make_info(m.group(1).strip(), m.group(2).strip(), lang)
    
    # 策略 F: [桜都字幕组][YYMMDD][res][extra][Studio]Title.ext
    m = re.match(r'\[桜都字幕[組组]?\]\[\d{6}\]\[[^\]]+\]\[[^\]]+\]\[([^\]]+)\](.+)\.(mp4|mkv)$', name)
    if m:
        return _make_info(m.group(1).strip(), m.group(2).strip(), _lang_from_dir(subdir))
    
    # 策略 G: 前作格式 [桜都字幕组] [Studio] Title.ext
    m = re.match(r'\[桜都字幕[組组]?\]\s*\[?([^\]]*)\]\s*(.+?)\.(chs\.mp4|cht\.mp4|mkv|mp4)$', name)
    if m:
        ext = m.group(3)
        lang = "CHS" if ext == "chs.mp4" else "CHT" if ext == "cht.mp4" else "RAW"
        return _make_info(m.group(1).strip(), m.group(2).strip(), lang)
    
    # 策略 H: 極彩花夢格式 [極彩花夢][Studio]Title [meta]...ext
    # 文件名示例: [極彩花夢][PoRO]懲らしめ2～狂育的デパガ指導～ 義妹デパガ・穂波～魅惑の漏らし男根～[1080P][x264_8bit][CHS].mp4
    m = re.match(r'\[極彩花夢\]\[([^\]]+)\](.+?)\.(chs\.mp4|cht\.mp4|mkv|mp4|chs_jpn\.mp4)$', name, re.IGNORECASE)
    if m:
        return _make_info(m.group(1).strip(), m.group(2).strip(), "CHS")
    
    # 策略 I: 無標題格式（無 [桜都字幕组] 前綴）[1080P] [極彩花夢][Studio]Title...
    m = re.match(r'\[[^\]]+\]\s*\[極彩花夢\]\[([^\]]+)\](.+?)\.(mp4|mkv)$', name)
    if m:
        return _make_info(m.group(1).strip(), m.group(2).strip(), _lang_from_dir(subdir))
    
    return None


def _lang_from_dir(subdir: str) -> str:
    """从子目录名推断语言"""
    s = subdir.upper()
    if s in ("CHS", "GB", "GB[简体]"): return "CHS"
    if s in ("CHT", "BIG5", "BIG5[繁体]"): return "CHT"
    return "RAW"


def _make_info(studio: str, rest: str, lang: str) -> dict:
    """从 studio + title_rest 构建信息"""
    title_clean = EPISODE_PAT.sub('', rest).strip()
    ep_num = _extract_ep(rest)
    
    # 归一化系列名
    norm = title_clean.strip("～").strip()
    norm = re.sub(r'\s*\[[^\]]*\]\s*$', '', norm).strip()
    norm = re.sub(r'^OVA[　\s]*', '', norm).strip()
    norm = re.sub(r'[　\s]*THE\s+ANIMATION\s*$', '', norm).strip()
    norm = norm.replace('!', '！').replace('?', '？')
    norm = re.sub(r'\s+[A-Z_0-9]+$', '', norm).strip()
    
    # 用 ～ 拆分取基础系列名
    parts = norm.split("～")
    if len(parts) >= 3:
        norm_series = "～".join(parts[:2]).strip()
    elif len(parts) == 2:
        norm_series = parts[0].strip()
    else:
        norm_series = norm
    
    series_key = f"[{studio}]{norm_series}"
    display = f"[{studio}]{norm_series}"
    
    return {
        "studio": studio, "title": title_clean, "ep_num": ep_num,
        "lang": lang, "series_key": series_key, "display_name": display,
    }


def _extract_ep(title: str) -> str:
    """提取话数标识，用于判断是否同一话"""
    m = re.search(r'(?:＃(\d+)|第([一二三四五六七八九十\d]+)[話巻]|([一二三四五六七八九十]+)話|[前中後上中下][編巻話編]|Vol\.?(\d+))', title)
    if m:
        parts = [g for g in m.groups() if g]
        return parts[0] if parts else "unknown"
    # 用 ～ 后的部分作为 episode 标识
    pts = title.strip("～").split("～")
    if len(pts) >= 3:
        return "～".join(pts[2:]).strip()[:30]
    elif len(pts) == 2:
        return pts[1].strip()[:30]
    return "full"


# ══════════════════════════════════════════════════════════════
# Phase 1: 全量扫描所有视频文件
# ══════════════════════════════════════════════════════════════
def scan_all_videos() -> dict:
    """扫描所有视频文件，返回 {series_key: {files, episodes, months, years}}"""
    data = defaultdict(lambda: {"files": [], "episodes": set(), "months": set(), "years": set()})
    total = 0
    
    # 排除目录
    skip_dirs = {"前作"}
    skip_prefix = ("海报", "预告", "封面")
    
    for year_dir in sorted(BASE.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.endswith("年合集"):
            continue
        y = year_dir.name
        
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir() or "月合集" not in month_dir.name:
                continue
            m = month_dir.name
            
            # 收集所有视频子目录
            vdirs = [d for d in month_dir.iterdir() if d.is_dir() 
                     and d.name not in skip_dirs
                     and not any(d.name.startswith(p) for p in skip_prefix)]
            
            # 扫描主目录下的视频
            for vd in vdirs:
                for f in sorted(vd.iterdir()):
                    if f.suffix not in (".mp4", ".mkv"):
                        continue
                    info = parse_video_filename(f.name, vd.name)
                    if not info:
                        continue
                    total += 1
                    sk = info["series_key"]
                    data[sk]["files"].append({
                        "path": str(f), "lang": info["lang"],
                        "ep_num": info["ep_num"], "size": f.stat().st_size,
                        "month": m, "year": y, "display": info["display_name"],
                    })
                    data[sk]["episodes"].add(info["ep_num"])
                    data[sk]["months"].add(m)
                    data[sk]["years"].add(y)
            
            # 扫描前作目录（去重）
            qz = month_dir / "前作"
            if qz.is_dir():
                for qs in sorted(qz.iterdir()):
                    if not qs.is_dir():
                        continue
                    for f in sorted(qs.iterdir()):
                        if f.suffix not in (".mp4", ".mkv"):
                            continue
                        info = parse_video_filename(f.name, "RAW")
                        if not info:
                            continue
                        sk = info["series_key"]
                        # 检查是否已有相同 ep_num+lang
                        dedup = False
                        for ef in data[sk]["files"]:
                            if ef["ep_num"] == info["ep_num"] and ef["lang"] == info["lang"]:
                                dedup = True
                                break
                        if not dedup:
                            total += 1
                            data[sk]["files"].append({
                                "path": str(f), "lang": info["lang"],
                                "ep_num": info["ep_num"], "size": f.stat().st_size,
                                "month": m, "year": y, "display": info["display_name"],
                            })
                            data[sk]["episodes"].add(info["ep_num"])
                            data[sk]["months"].add(m)
                            data[sk]["years"].add(y)
    
    print(f"   扫描文件: {total}")
    return data


# ══════════════════════════════════════════════════════════════
# Phase 2: 匹配周边媒体
# ══════════════════════════════════════════════════════════════
def match_media(series_data: dict) -> dict:
    """扫描海报/封面/简评，匹配到系列"""
    media = defaultdict(lambda: {"posters": [], "jpgs": [], "reviews": []})
    all_reviews = {}
    
    # 为快速匹配，建立 series_key → 纯标题的映射
    title_map = {}
    for sk in series_data:
        t = sk.split("]", 1)[-1].strip() if "]" in sk else sk
        title_map[sk] = t
    
    for year_dir in sorted(BASE.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.endswith("年合集"):
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir() or "月合集" not in month_dir.name:
                continue
            m = month_dir.name
            
            # 海报/封面目录
            media_dirs = [d for d in month_dir.iterdir() 
                         if d.is_dir() and ("海报" in d.name or d.name == "封面")]
            for md in media_dirs:
                for f in sorted(md.iterdir()):
                    if f.suffix not in (".png", ".jpg", ".webp", ".jpeg"):
                        continue
                    stem = f.stem
                    clean = re.sub(r'^\[封面\]', '', stem)
                    clean = EPISODE_PAT.sub('', clean).strip()
                    best = _match_to_series(clean, title_map)
                    if best:
                        if f.suffix == ".jpg":
                            media[best]["jpgs"].append(str(f))
                        else:
                            media[best]["posters"].append(str(f))
            
            # 前作中的图片
            qz = month_dir / "前作"
            if qz.is_dir():
                for qs in sorted(qz.iterdir()):
                    if not qs.is_dir():
                        continue
                    for f in sorted(qs.iterdir()):
                        if f.suffix not in (".png", ".jpg", ".webp", ".jpeg"):
                            continue
                        stem = f.stem
                        clean = re.sub(r'^\[封面\]|^\[预览\]', '', stem)
                        clean = EPISODE_PAT.sub('', clean).strip()
                        best = _match_to_series(clean, title_map)
                        if best:
                            if f.suffix == ".jpg":
                                media[best]["jpgs"].append(str(f))
                            else:
                                media[best]["posters"].append(str(f))
            
            # 简评
            for f in sorted(month_dir.iterdir()):
                if f.name.endswith(".txt") and "简评" in f.name:
                    all_reviews[m] = str(f)
    
    # 解析简评并匹配
    rev_entries = _parse_reviews(all_reviews)
    for work_name, entries in rev_entries.items():
        for sk, t in title_map.items():
            if work_name == t or t.startswith(work_name) or work_name in t or t in work_name:
                for e in entries:
                    media[sk]["reviews"].append(e)
                break
    
    return media


def _longest_common_prefix(a: str, b: str) -> str:
    """返回两个字符串的最长公共前缀"""
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return a[:i]


def apply_ai_merges(data: dict) -> int:
    """AI 语义合并：把同一系列的不同命名统一到规范名称下"""
    # AI 生成的合并映射 (旧key → 新key)
    # 基于对全量系列名的语义分析
    MERGE_MAP = {
        # ── [PoRO] ──
        "[PoRO]エロリーマン へっぽこ高飛車・梨々香": "[PoRO]エロリーマン",
        "[PoRO]エロリーマン ナマイキポジロン・梨々香": "[PoRO]エロリーマン",
        "[PoRO]エロリーマン 真苛面目られッ娘・美冬": "[PoRO]エロリーマン",
        "[PoRO]エロリーマン2 エロ輩姉妹真冬＆愛菜": "[PoRO]エロリーマン2",
        "[PoRO]エロリーマン2 憧憬クルエロ・真冬": "[PoRO]エロリーマン2",
        "[PoRO]エロ医師 ナマイキドエロ・怜奈＆綾乃": "[PoRO]エロ医師",
        "[PoRO]エロ医師 ワイセツチン療・綾乃＆怜奈": "[PoRO]エロ医師",
        "[PoRO]エロ医師 清純ドエロ・綾乃": "[PoRO]エロ医師",
        "[PoRO]エロ医師 清純無垢っつり綾乃": "[PoRO]エロ医師",
        "[PoRO]ツグナヒ ナマイキスポ処女・ナツキ": "[PoRO]ツグナヒ",
        "[PoRO]ツグナヒ 潔癖生真面目・葵": "[PoRO]ツグナヒ",
        "[PoRO]ツグナヒ 褐色ビチギャル・茗子": "[PoRO]ツグナヒ",
        "[PoRO]ツグナヒ 高飛車お姫様・瑠璃子": "[PoRO]ツグナヒ",
        "[PoRO]灼炎のエリス ケツ穴過敏勇者・エリス": "[PoRO]灼炎のエリス",
        "[PoRO]灼炎のエリス 堕落雌豚勇者・エリス": "[PoRO]灼炎のエリス",
        "[PoRO]灼炎のエリス 尻床野菜勇者・エリス": "[PoRO]灼炎のエリス",
        "[PoRO]灼炎のエリス 美少女へっぽこ勇者・エリス": "[PoRO]灼炎のエリス",
        "[PoRO]魔剣の姫はエロエロです ツンデレ姫騎士の矮小鎧前罵詈後突": "[PoRO]魔剣の姫はエロエロです",
        "[PoRO]支配の教壇 ドジへっぽ娘教師・琴実": "[PoRO]支配の教壇",
        "[PoRO]支配の教壇 無口養護教諭・アンナ": "[PoRO]支配の教壇",
        "[PoRO]支配の教壇 爆乳ドS女教師・美璃亜～淫虐スパルタクリップ": "[PoRO]支配の教壇",
        "[PoRO]あねちじょマックスハート 変態かてきょ·更紗": "[PoRO]あねちじょマックスハート",
        "[PoRO]あねちじょマックスハート 媚姉誘淫ファミレス風・更紗": "[PoRO]あねちじょマックスハート",
        "[PoRO]姫様LOVEライフ！ ツインテ生意気姫様·舞華": "[PoRO]姫様LOVEライフ！",
        "[PoRO]姫様LOVEライフ！ ツインテ生意気姫様・舞華": "[PoRO]姫様LOVEライフ！",
        "[PoRO]姫様LOVEライフ！ ナマイキビキニ姫・舞華": "[PoRO]姫様LOVEライフ！",
        "[PoRO]姫様LOVEライフ！ 清楚ではしたない王女・ルリア": "[PoRO]姫様LOVEライフ！",
        "[PoRO]姫様LOVEライフ！ 自虐オ姫・ラティ": "[PoRO]姫様LOVEライフ！",
        "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！ ご奉仕M令嬢・イリナ": "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！",
        "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！ ご奉仕執事・セレスティン": "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！",
        "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！ 緊縛ドMお嬢様・イリナ": "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！",
        "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！ 緊縛執事・セレスティン": "[PoRO]完璧お嬢様の私が土下座でマゾ堕ちするちょろインなワケないですわ！",
        "[PoRO]DearestBlue": "[PoRO]DearestBlue",
        "[PoRO]White Blue": "[PoRO]DearestBlue",
        "[PoRO]三射面談～連鎖する恥辱·調教の学園": "[PoRO]三射面談～連鎖する恥辱・調教の学園",
        "[PoRO]妖魔娼館へようこそ": "[PoRO]妖魔娼館へようこそ",
        "[PoRO]のぞき彼女 「見つめる優等生 楓": "[PoRO]のぞき彼女",
        
        # ── [ばにぃうぉ～か～] ──
        "[ばにぃうぉ～か～]じょしラク！ ＃3セル版": "[ばにぃうぉ～か～]じょしラク！",
        "[ばにぃうぉ～か～]じょしラク！ ＃4セル版": "[ばにぃうぉ～か～]じょしラク！",
        "[ばにぃうぉ～か～]催眠性指導 ＃1 小幡優衣の場合": "[ばにぃうぉ～か～]催眠性指導",
        "[ばにぃうぉ～か～]催眠性指導 ＃2 倉敷玲奈の場合": "[ばにぃうぉ～か～]催眠性指導",
        "[ばにぃうぉ～か～]催眠性指導 ＃3 宮島桜の場合": "[ばにぃうぉ～か～]催眠性指導",
        "[ばにぃうぉ～か～]催眠性指導 ＃4宮島椿の場合": "[ばにぃうぉ～か～]催眠性指導",
        "[ばにぃうぉ～か～]聖華女学院公認竿おじさん ＃1 セル版": "[ばにぃうぉ～か～]聖華女学院公認竿おじさん",
        "[ばにぃうぉ～か～]聖華女学院公認竿おじさん ＃2 セル版": "[ばにぃうぉ～か～]聖華女学院公認竿おじさん",
        "[ばにぃうぉ～か～]ovaちーちゃん開発日記": "[ばにぃうぉ～か～]まこちゃん開発日記",
        "[ばにぃうぉ～か～]ようこそ！スケベエルフの森へ ＃3 エルフとダークエルフの全面対決！ 救世主様と『らぶらぶ子作り対決』": "[ばにぃうぉ～か～]スケベエルフ探訪記",
        "[ばにぃうぉ～か～]ようこそ！スケベエルフの森へ ＃4 エルフもダークエルフも仲良く子作り！ 救世主様と『ハーレム生活』": "[ばにぃうぉ～か～]スケベエルフ探訪記",
        
        # ── [Queen Bee] ──
        "[Queen Bee]Sweet and Hot1": "[Queen Bee]Sweet and Hot",
        "[Queen Bee]Sweet and Hot2［紙魚丸］": "[Queen Bee]Sweet and Hot",
        "[Queen Bee]おにちちハーレム 第2話": "[Queen Bee]おにちちハーレム",
        "[Queen Bee]おにちちハーレム 第3話": "[Queen Bee]おにちちハーレム",
        "[Queen Bee]おにちちハーレム 第4話": "[Queen Bee]おにちちハーレム",
        "[Queen Bee]ひみつのきち1": "[Queen Bee]ひみつのきち",
        "[Queen Bee]ひみつのきち2宵": "[Queen Bee]ひみつのきち",
        "[Queen Bee]アオハルスナッチ1": "[Queen Bee]アオハルスナッチ",
        "[Queen Bee]アオハルスナッチ2［夏庵］": "[Queen Bee]アオハルスナッチ",
        "[Queen Bee]キスハグ 1［水平 線］": "[Queen Bee]キスハグ",
        "[Queen Bee]キスハグ 2［水平 線］": "[Queen Bee]キスハグ",
        "[Queen Bee]サキュバスアプリ ～学園催": "[Queen Bee]サキュバスアプリ",
        "[Queen Bee]サキュバスアプリ～学園催眠": "[Queen Bee]サキュバスアプリ",
        "[Queen Bee]ハニーブロンド2 第1話": "[Queen Bee]ハニーブロンド2",
        "[Queen Bee]ハニーブロンド2 第2話": "[Queen Bee]ハニーブロンド2",
        "[Queen Bee]ハニーブロンド2 第3話": "[Queen Bee]ハニーブロンド2",
        "[Queen Bee]ハニーブロンド2 第4話": "[Queen Bee]ハニーブロンド2",
        "[Queen Bee]ヒナギクヴァージンロストクラブへようこそ1": "[Queen Bee]ヒナギクヴァージンロストクラブへようこそ",
        "[Queen Bee]ヒナギクヴァージンロストクラブへようこそ2": "[Queen Bee]ヒナギクヴァージンロストクラブへようこそ",
        "[Queen Bee]亜人がお好きなんですね 第1話": "[Queen Bee]亜人がお好きなんですね",
        "[Queen Bee]亜人がお好きなんですね 第2話": "[Queen Bee]亜人がお好きなんですね",
        "[Queen Bee]少年が大人になった夏 第二話": "[Queen Bee]少年が大人になった夏",
        "[Queen Bee]少年が大人になった夏 第四話": "[Queen Bee]少年が大人になった夏",
        "[Queen Bee]人妻、蜜と肉": "[Queen Bee]人妻、蜜と肉",
        "[Queen Bee]人妻、蜜と肉 第一巻「月野定規」": "[Queen Bee]人妻、蜜と肉",
        "[Queen Bee]人妻、蜜と肉 第二巻［月野定規］": "[Queen Bee]人妻、蜜と肉",
        "[Queen Bee]人妻、蜜と肉 第三巻［月野定規］": "[Queen Bee]人妻、蜜と肉",
        "[Queen Bee]人妻、蜜と肉 第四巻［月野定規］": "[Queen Bee]人妻、蜜と肉",
        "[Queen Bee]僕と先生と友達のママ": "[Queen Bee]僕と先生と友達のママ",
        "[Queen Bee]僕と先生と友達のママ 前編": "[Queen Bee]僕と先生と友達のママ",
        "[Queen Bee]村又さんの秘密": "[Queen Bee]村又さんの秘密",
        "[Queen Bee]村又さんの秘密 下巻 [AVC_AAC][720P]": "[Queen Bee]村又さんの秘密",
        "[Queen Bee]村又さんの秘密 下巻 [Y410][HEVC_AAC][1080P]": "[Queen Bee]村又さんの秘密",
        "[Queen Bee]故に人妻は寝取られた。 第一巻": "[Queen Bee]故に人妻は寝取られた。",
        "[Queen Bee]故に人妻は寝取られた。第二巻［あらくれ］": "[Queen Bee]故に人妻は寝取られた。",
        
        # ── [nur] ──
        "[nur]小さな蕾のその奥に…": "[nur]小さな蕾のその奥に…",
        "[nur]小さな蕾のその奥に……": "[nur]小さな蕾のその奥に…",
        "[nur]小さな蕾のその奥に…… ～剥き散らされる儚い蕾": "[nur]小さな蕾のその奥に…",
        "[nur]未必の恋": "[nur]未必の恋",
        "[nur]未必の恋 〜カレシの彼女〜": "[nur]未必の恋",
        "[nur]そしてわたしはおじさんに…… 「契られた裏切り」": "[nur]そしてわたしは",
        "[nur]そしてわたしはおじさんに…… 「色褪せた憎しみ」": "[nur]そしてわたしは",
        "[nur]姉辱尽くし": "[nur]姉辱尽くし",
        "[nur]卑触家のルール": "[nur]卑触家のルール",
        
        # ── [鈴木みら乃] ──
        "[鈴木みら乃]自宅警備員 ターゲットさやか": "[鈴木みら乃]自宅警備員",
        "[鈴木みら乃]自宅警備員 ターゲット由紀": "[鈴木みら乃]自宅警備員",
        "[鈴木みら乃]自宅警備員2 第一話 巨乳エリート従兄妹・玲奈": "[鈴木みら乃]自宅警備員2",
        "[鈴木みら乃]自宅警備員2 第一話 巨乳エリート従兄妹・玲奈 ～奪われる純潔": "[鈴木みら乃]自宅警備員2",
        "[鈴木みら乃]自宅警備員2 第二話 巨乳エリート従兄妹・玲奈": "[鈴木みら乃]自宅警備員2",
        "[鈴木みら乃]自宅警備員2 第三話 爆乳未亡人叔母・志保": "[鈴木みら乃]自宅警備員2",
        "[鈴木みら乃]自宅警備員2 第四話 爆乳未亡人叔母・志保": "[鈴木みら乃]自宅警備員2",
        "[鈴木みら乃]コンビニ○○Z 第四話 あなた、コンビニマネですよね。本社に万引きがバレていいんですか？": "[鈴木みら乃]コンビニ少女Z",
        "[鈴木みら乃]コンビニ少女Z 第一話 あなた、地下アイドルですよね。社長に万引きがバレていいんですか？": "[鈴木みら乃]コンビニ少女Z",
        "[鈴木みら乃]コンビニ少女Z 第二話 あなた、お茶汲みOLですよねお。会社に万引きがバレていいんですか？": "[鈴木みら乃]コンビニ少女Z",
        "[鈴木みら乃]くノ一○○伝 紫陽花 第一話 潜入、蒲生邸 媚薬拷問と快楽調教": "[鈴木みら乃]くノ一○○伝 紫陽花",
        "[鈴木みら乃]くノ一○○伝 紫陽花 第二話 悪徳商人、越後屋 白濁に咲くは悪の華": "[鈴木みら乃]くノ一○○伝 紫陽花",
        "[鈴木みら乃]くノ一○○伝 紫陽花 第二話 悪徳商人、越後屋 白濁に咲くは悪の華.chschs": "[鈴木みら乃]くノ一○○伝 紫陽花",
        "[鈴木みら乃]卒業○○電車 一輌目 思い出の○リ巨乳教師は狙われている": "[鈴木みら乃]卒業○○電車",
        "[鈴木みら乃]卒業○○電車 二輌目 女教師の尻はいつも後ろから見られている": "[鈴木みら乃]卒業○○電車",
        "[鈴木みら乃]卒業○○電車 三輌目 酔いつぶれた女教師は弛緩した身体を弄ばれる": "[鈴木みら乃]卒業○○電車",
        "[鈴木みら乃]俺が姪（かのじょ）を○す理由（わけ） 五日目 彼女はその日から身体で稼ぐようになった": "[鈴木みら乃]俺が姪（かのじょ）を○す理由（わけ）",
        "[鈴木みら乃]俺が姪（かのじょ）を○す理由（わけ） 六日目 彼女はその日ようやく親離れができた": "[鈴木みら乃]俺が姪（かのじょ）を○す理由（わけ）",
        
        # ── [BOMB! CUTE! BOMB!] ──
        "[BOMB! CUTE! BOMB!]ニプルへイムの狩人 第1話 淫紋は妖しく輝く": "[BOMB! CUTE! BOMB!]ニプルへイムの狩人",
        "[BOMB! CUTE! BOMB!]ニプルへイムの狩人 第2話 絶頂、絶頂、絶頂！": "[BOMB! CUTE! BOMB!]ニプルへイムの狩人",
        "[BOMB! CUTE! BOMB!]メルティス・クエスト#1": "[BOMB! CUTE! BOMB!]メルティス・クエスト",
        "[BOMB! CUTE! BOMB!]メルティス・クエスト#2": "[BOMB! CUTE! BOMB!]メルティス・クエスト",
        "[BOMB! CUTE! BOMB!]素晴らしき国家の築き方#1": "[BOMB! CUTE! BOMB!]素晴らしき国家の築き方",
        "[BOMB! CUTE! BOMB!]素晴らしき国家の築き方#2": "[BOMB! CUTE! BOMB!]素晴らしき国家の築き方",
        
        # ── [せるふぃっしゅ] ──
        "[せるふぃっしゅ]ガキにもどって犯りなおしっ！！！ #1": "[せるふぃっしゅ]ガキにもどって犯りなおしっ！！！",
        "[せるふぃっしゅ]ガキにもどって犯りなおしっ！！！ #2": "[せるふぃっしゅ]ガキにもどって犯りなおしっ！！！",
        
        # ── 解析错误修复 ──
        "[720P Hi10P]": None,  # 删除
        "[720P]": None,  # 删除
    }
    
    merged = 0
    for old_key, new_key in list(MERGE_MAP.items()):
        if old_key not in data:
            continue
        if new_key is None:
            # 删除错误解析的条目
            del data[old_key]
            merged += 1
            continue
        if old_key == new_key:
            continue
        
        # 合并到新 key
        if new_key not in data:
            data[new_key] = {"files": [], "episodes": set(), "months": set(), "years": set()}
        
        for f in data[old_key]["files"]:
            f["display"] = new_key
            data[new_key]["files"].append(f)
            data[new_key]["episodes"].add(f["ep_num"])
        data[new_key]["months"].update(data[old_key]["months"])
        data[new_key]["years"].update(data[old_key]["years"])
        del data[old_key]
        merged += 1
    
    return merged


def _match_to_series(clean: str, title_map: dict) -> str:
    """匹配媒体文件名到系列"""
    best_key, best_score = None, 0
    for sk, t in title_map.items():
        if t == clean:
            return sk
        score = len(set(t) & set(clean))
        if score > best_score:
            best_score = score
            best_key = sk
    if best_score >= 4:
        return best_key
    return None


def _parse_reviews(all_reviews: dict) -> dict:
    entries = defaultdict(list)
    for month, fp in all_reviews.items():
        try:
            with open(fp, "r", encoding="utf-8") as f:
                c = f.read()
        except:
            try:
                with open(fp, "r", encoding="gbk") as f:
                    c = f.read()
            except:
                continue
        parts = re.split(r'《([^》]+)》', c)
        if len(parts) >= 3:
            for i in range(1, len(parts)-1, 2):
                wn = parts[i].strip()
                rt = parts[i+1].strip()
                if wn and rt:
                    entries[wn].append({"month": month, "text": f"《{wn}》\n{rt}"})
    return entries


# ══════════════════════════════════════════════════════════════
# Phase 3: 创建目录和硬链接
# ══════════════════════════════════════════════════════════════
def create_output(series_data: dict, media: dict):
    """按系列创建目录和硬链接"""
    # 过滤：多集系列
    multi = {k: v for k, v in series_data.items() if len(v["episodes"]) >= 2}
    single = {k: v for k, v in series_data.items() if len(v["episodes"]) < 2}
    
    print(f"   多集系列: {len(multi)}")
    print(f"   单集跳过: {len(single)}")
    
    stats = {"series": 0, "videos": 0, "posters": 0, "jpgs": 0, "reviews": 0, "links": 0}
    
    for sk, sd in sorted(multi.items()):
        # 取第一个 display_name 作为目录名
        displays = set(f["display"] for f in sd["files"])
        dn = sk  # fallback
        for d in sorted(displays):
            dn = d
            if "OVA" in d:
                break
        
        safe = dn.replace("/", "／").replace("\\", "／").replace(":", "：")
        sdir = OUTPUT / safe
        sdir.mkdir(parents=True, exist_ok=True)
        stats["series"] += 1
        print(f"\n📁 {dn}")
        
        # 视频（去重）
        seen = set()
        for fi in sorted(sd["files"], key=lambda x: x["path"]):
            ld = {"BIG5": "CHT", "GB": "CHS", "CHS": "CHS", "CHT": "CHT"}.get(fi["lang"], "RAW")
            dedup = f"{fi['ep_num']}_{ld}"
            if dedup in seen:
                continue
            seen.add(dedup)
            src = fi["path"]
            dst = sdir / ld / Path(src).name
            dst.parent.mkdir(exist_ok=True)
            if not dst.exists():
                try:
                    os.link(src, dst)
                except Exception as e:
                    print(f"  ❌ {Path(src).name}: {e}")
                    continue
            stats["videos"] += 1
            stats["links"] += 1
        
        # 海报（直接放系列根目录）
        seen_p = set()
        if sk in media and media[sk]["posters"]:
            for p in media[sk]["posters"]:
                pn = Path(p).name
                if pn in seen_p:
                    continue
                seen_p.add(pn)
                dst = sdir / pn
                if not dst.exists():
                    try:
                        os.link(p, str(dst))
                    except:
                        continue
                stats["posters"] += 1
                stats["links"] += 1
        
        # 封面（直接放系列根目录）
        seen_j = set()
        if sk in media and media[sk]["jpgs"]:
            for j in media[sk]["jpgs"]:
                jn = Path(j).name
                if jn in seen_j:
                    continue
                seen_j.add(jn)
                dst = sdir / jn
                if not dst.exists():
                    try:
                        os.link(j, str(dst))
                    except:
                        continue
                stats["jpgs"] += 1
                stats["links"] += 1
        
        # 简评
        if sk in media and media[sk]["reviews"]:
            texts = []
            for entry in media[sk]["reviews"]:
                ml = entry["month"].replace("[桜都字幕组]", "")
                texts.append(f"【{ml}】\n{entry['text']}\n---\n")
            if texts:
                with open(sdir / "简评.txt", "w", encoding="utf-8") as f:
                    f.write(f"《{dn}》简评汇总\n" + "=" * 40 + "\n\n" + "\n".join(texts))
                stats["reviews"] += 1
    
    # 报告
    print(f"\n{'='*50}")
    print("✅ 完成！")
    print(f"{'='*50}")
    for k, v in stats.items():
        print(f"   {k}: {v}")
    print(f"\n   目录: {OUTPUT}")
    
    # 保存单集清单
    with open(OUTPUT / "_单集作品清单.txt", "w", encoding="utf-8") as f:
        f.write(f"单集作品（跳过），共 {len(single)} 个\n\n")
        for sk in sorted(single.keys()):
            f.write(f"{sk}\n")
            for fi in single[sk]["files"][:3]:
                f.write(f"  - {Path(fi['path']).name}\n")
            f.write("\n")


if __name__ == "__main__":
    print("🔍 Phase 1: 全量扫描视频...")
    series_data = scan_all_videos()
    print(f"   识别系列: {len(series_data)}")
    
    # ── AI 语义合并 ──
    merged = apply_ai_merges(series_data)
    if merged > 0:
        print(f"   智能合并: {merged} 组合并")
    
    print("\n🔍 Phase 2: 匹配周边媒体...")
    media = match_media(series_data)
    print(f"   匹配海报: {sum(len(m['posters']) for m in media.values())}")
    print(f"   匹配封面: {sum(len(m['jpgs']) for m in media.values())}")
    print(f"   匹配简评: {sum(len(m['reviews']) for m in media.values())}")
    
    print(f"\n🔨 Phase 3: 创建目录...")
    create_output(series_data, media)

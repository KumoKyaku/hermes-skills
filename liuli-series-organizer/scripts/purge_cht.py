#!/usr/bin/env python3
"""删除琉璃神社库里的繁体（CHT）视频，只为有简体对应的那部分。

用法:
    python purge_cht.py            # dry-run，只统计
    python purge_cht.py --delete   # 真删

要点:
- CHT 在「原始合集」和「按系列」（硬链接）两处都有，必须都删才释放空间
- 按 (st_dev, st_ino) 去重算真实释放量
- 以「月合集/系列目录」为单位递归查 base_key，只有繁体没简体的作品自动保留
"""
import sys, os, re

DRY = "--delete" not in sys.argv
ROOT_LIULI = r"E:\SystemCacheInfo\琉璃神社"
ROOT_SERIES = r"E:\SystemCacheInfo\琉璃神社_按系列"


def is_cht(fn):
    return fn.lower().endswith((".cht.mp4", ".cht.mkv", ".cht.wmv"))


def is_chs(fn):
    return fn.lower().endswith((".chs.mp4", ".chs.mkv", ".chs.wmv"))


def base_key(fn):
    return re.sub(r'\.(chs|cht)\.(mp4|mkv|wmv)$', '', fn, flags=re.I)


# 1) 扫描单元 = 月合集目录 + 按系列目录
units = []
for y in sorted(os.listdir(ROOT_LIULI)):
    yp = os.path.join(ROOT_LIULI, y)
    if os.path.isdir(yp) and y.endswith("年合集"):
        for m in sorted(os.listdir(yp)):
            mp = os.path.join(yp, m)
            if os.path.isdir(mp):
                units.append(mp)
if os.path.isdir(ROOT_SERIES):
    for n in sorted(os.listdir(ROOT_SERIES)):
        sp = os.path.join(ROOT_SERIES, n)
        if os.path.isdir(sp):
            units.append(sp)

# 2) 找孤儿（只有繁体）→ 保留
keep = set()
for u in units:
    cht, chs = [], set()
    for dp, dn, fns in os.walk(u):
        for f in fns:
            if is_cht(f):
                cht.append(os.path.join(dp, f))
            elif is_chs(f):
                chs.add(base_key(f))
    for p in cht:
        if base_key(os.path.basename(p)) not in chs:
            keep.add(p.lower())

# 3) 收集待删
# 注意：keep 只记了路径，但按系列里的硬链接副本要一起保留（同 base_key 同作品）
keep_keys = set(base_key(os.path.basename(p)) for p in keep)
targets = []
for root in (ROOT_LIULI, ROOT_SERIES):
    for dp, dn, fns in os.walk(root):
        for f in fns:
            if is_cht(f) and base_key(f) not in keep_keys:
                targets.append(os.path.join(dp, f))

# 4) 算真实释放
seen = {}
for p in targets:
    try:
        st = os.stat(p)
        seen[(st.st_dev, st.st_ino)] = st.st_size
    except OSError:
        pass
real = sum(seen.values())

print(f"{'[DRY-RUN] ' if DRY else ''}待删 CHT: {len(targets)} 个 / {len(seen)} 独立 inode")
print(f"预计释放: {real / 1024 ** 3:.2f} GiB   保留孤儿: {len(keep_keys)} 部")

if DRY:
    print("未删除。加 --delete 执行。")
    sys.exit(0)

ok, fail = 0, []
for p in targets:
    try:
        os.remove(p)
        ok += 1
    except Exception as e:
        fail.append((p, str(e)))

# 5) 清理空 CHT/BIG5 目录
removed = 0
for root in (ROOT_LIULI, ROOT_SERIES):
    for dp, dn, fns in os.walk(root, topdown=False):
        if os.path.basename(dp).upper() in ("CHT", "BIG5") and not os.listdir(dp):
            try:
                os.rmdir(dp)
                removed += 1
            except OSError:
                pass

print(f"已删除 {ok} 个，失败 {len(fail)}，清理空目录 {removed} 个，释放 {real / 1024 ** 3:.2f} GiB")
for f, e in fail[:10]:
    print("  ", f, e)

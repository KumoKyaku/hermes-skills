import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DRY = "--delete" not in sys.argv
ROOT_LIULI = r"E:\SystemCacheInfo\琉璃神社"
ROOT_SERIES = r"E:\SystemCacheInfo\琉璃神社_按系列"

SIMPLIFIED_DIRS = {"CHS", "GB"}


def is_video(fn):
    return fn.lower().endswith((".mp4", ".mkv", ".wmv"))


def is_simplified(fn, dirpath):
    d = os.path.basename(dirpath).upper()
    l = fn.lower()
    if d in SIMPLIFIED_DIRS:
        return True
    if l.endswith((".chs.mp4", ".chs.mkv")):
        return True
    if re.search(r'\[(?:720P|1080P|Ma10p|Hi10P)?\s*GB\s*\]', fn, flags=re.I):
        return True
    return False


def norm_key(fn):
    n = os.path.splitext(fn)[0]
    n = re.sub(r'^(?:\[[^\]]{1,14}\]\s*)+', '', n)
    n = re.sub(r'\[(?:720P|1080P|Ma10p|Hi10P|HEVC|AVC_AAC|HEVC_AAC)[^\]]*\]', ' ', n, flags=re.I)
    n = re.sub(r'\[?\s*(?:GB|BIG5)\s*\]?', '', n, flags=re.I)
    n = re.sub(r'\.(chs|cht)$', '', n, flags=re.I)
    return re.sub(r'[\s_]+', '', n)


units = []
for y in sorted(os.listdir(ROOT_LIULI)):
    yp = os.path.join(ROOT_LIULI, y)
    if os.path.isdir(yp) and y.endswith("年合集"):
        for m in sorted(os.listdir(yp)):
            mp = os.path.join(yp, m)
            if os.path.isdir(mp):
                units.append(mp)
for n in sorted(os.listdir(ROOT_SERIES)):
    sp = os.path.join(ROOT_SERIES, n)
    if os.path.isdir(sp):
        units.append(sp)

keep_keys = set()
orphan_units = {}
for u in units:
    others, chss = [], set()
    for dp, dn, fns in os.walk(u):
        for f in fns:
            if not is_video(f):
                continue
            if is_simplified(f, dp):
                chss.add(norm_key(f))
            else:
                others.append((f, os.path.join(dp, f)))
    for f, p in others:
        if norm_key(f) not in chss:
            keep_keys.add(norm_key(f))
            orphan_units.setdefault(u, 0)
            orphan_units[u] += 1

print(f"只有非简体版的作品(保留): {len(keep_keys)} 部，跨 {len(orphan_units)} 个月份/系列目录")

targets = []
for root in (ROOT_LIULI, ROOT_SERIES):
    for dp, dn, fns in os.walk(root):
        for f in fns:
            if is_video(f) and not is_simplified(f, dp) and norm_key(f) not in keep_keys:
                targets.append(os.path.join(dp, f))

seen = {}
for p in targets:
    try:
        st = os.stat(p)
        seen[(st.st_dev, st.st_ino)] = st.st_size
    except OSError:
        pass
real = sum(seen.values())

print(f"\n{'[DRY-RUN] ' if DRY else ''}待删非简体视频: {len(targets)} 个 / {len(seen)} 独立 inode")
print(f"预计释放: {real/1024**3:.2f} GiB")

if DRY:
    from collections import Counter
    c = Counter()
    for p in targets:
        c[os.path.basename(os.path.dirname(p))] += 1
    print("按目录分布:", dict(c))
    print("未删除。加 --delete 执行。")
    sys.exit(0)

ok, fail = 0, []
for p in targets:
    try:
        os.remove(p)
        ok += 1
    except Exception as e:
        fail.append((p, str(e)))

removed = 0
for root in (ROOT_LIULI, ROOT_SERIES):
    for dp, dn, fns in os.walk(root, topdown=False):
        if os.path.basename(dp).upper() in ("RAW", "CHT", "BIG5", "720P", "720P HI10P", "HEVC", "MA10P") and not os.listdir(dp):
            try:
                os.rmdir(dp)
                removed += 1
            except OSError:
                pass

print(f"已删除 {ok} 个，失败 {len(fail)}，清理空目录 {removed} 个")
print(f"释放: {real/1024**3:.2f} GiB")
for f, e in fail[:10]:
    print("  ", f, e)

# 琉璃神社月度合集下载流程

用户每月例行任务：下载琉璃神社最新月度合集（里番合集包，约 11-12 GiB/月）。

## 本地目录约定

```
E:/SystemCacheInfo/琉璃神社/20XX年合集/20XX年MM月合集/
```
- 2026 年已存：01-05 月（04/05 月通过 FDM 下载成功）
- 合集发布滞后：N 月合集约在 N+1 月月中发布（如 6 月合集 7/16 发布，7 月合集 8 月中才出）

## 域名现状（2026-08 验证）

- **hacg.ist** ✅ 可用（主站，WordPress，路径 /wp/）
- hacg.casa / hacg.la ✅ 可用（镜像，图片 CDN 域名）
- hacg.icu ❌ 已挂（旧域名，2026-06 时可用）
- liuli.in 及常见变体 ❌ 全部连不上

## 查找流程

1. 站内搜索（curl 或浏览器均可）：
   ```
   https://hacg.ist/wp/?s=2026年6月合集
   ```
   搜索结果标题形如 `"2026年6月合集"的搜索结果 – 琉璃神社 ★ HACG.LA`。

2. 打开合集文章页，URL 模式：`https://hacg.ist/wp/all/anime/2026%e5%b9%b46%e6%9c%88%e5%90%88%e9%9b%86/`

3. **提取磁力 hash**：文章正文里唯一的 40 位 hex 就是整月合集包的 btih。
   ```bash
   curl -s -m 15 -L "<文章URL>" -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" | \
     grep -oE "[0-9a-f]{40}" | sort -u
   ```
   验证方法：对比本地已有月份的页面 hash 与已知磁力（如 2026年03月页面 hash = `7cb8cbcf9b5c11bdffe70b960869406ae59d1163`，与历史记录一致），确认"页面唯一 hash = 整月包"。
   注意：页面可能包含单部作品的 hash 段落，但整月包 hash 通常就是页面唯一的 40-hex 串。

## 下载：aria2c 直连大概率失败，用 FDM

**症状**：aria2c 能拿到元数据（`[MEMORY][METADATA]` 117KiB 下载完成，总大小 11GiB 可见），连接大量 peer（CN:50-80），但 `DL:0B` 持续 —— GFW 掐 BT 数据流（同 IPZZ-276 案例）。

**有效方案：Free Download Manager（FDM）**

```bash
# FDM 是 GUI 程序：必须 background 启动（前台会卡到超时）
terminal(background=true, command="cd '/d/Program Files/Softdeluxe/Free Download Manager' && ./fdm.exe '<magnet>'")
```

- FDM 收到 magnet 后会**弹窗等待用户确认保存路径**（任务不会自动进队列）
- 需要用户手动：确认保存路径 → `E:\SystemCacheInfo\琉璃神社\2026年合集\2026年06月合集\` → 点下载
- 这就是 2026-06 时 04/05 月合集的下载方式，用户熟悉该操作
- 可截图确认 FDM 窗口已弹出（`fdm_check.png` 流程，见 windows-desktop-control 技能）

## ⚠️ 嵌套目录坑（2026-08 实战踩坑）

琉璃神社月合集种子的**顶层文件夹名与目标目录同名**（如 `2026年06月合集`）。

- **aria2c 下载时**：在目标目录内又建一个同名目录（`2026年06月合集/2026年06月合集/`），
  里面全是 **0 字节占位文件 + 空目录**（种子目录结构占位），下载失败后残留 → 24K 垃圾壳。
- **FDM 下载时**：检测到种子顶层文件夹与目标目录同名 → **直接平铺写入目标目录**，无嵌套。

**处理**：
1. 下载完成后必须验证目录结构（对照 04/05 月合集：`MM月海报/ 下月预告/ 简评.txt CHS/ CHT/ Fonts.zip RAW/ Subs.zip` 平铺）
2. 发现 `X月合集/X月合集/` 嵌套空壳：先确认 `find -type f -size +0` 无非空文件，再 `rm -rf` 嵌套层
3. 同时清理 `.aria2` 控制文件残留（`rm -f *.aria2`）

## FDM 内部状态可查

**FDM 内部状态可查**（只读诊断，勿在 FDM 运行时写）：
```
C:/Users/Sun47/AppData/Local/Free Download Manager/fdm.sqlite
- downloads 表：id/state/name/url/hash/filePath（state=1 排队中, 4=已完成）
- Torrents 表：BT 种子详情
```

## 备用思路（未验证，仅记录）

- 琉璃神社官方"不提供下载链接"（文章底部有免责声明），磁力 hash 是作者直接贴正文里的
- 评论区可能有补链，但官方警告"不要点击评论区不明链接"（防诈骗）

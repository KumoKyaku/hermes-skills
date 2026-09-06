# 琉璃神社月度合集下载流程

用户每月例行任务：下载琉璃神社最新月度合集（里番合集包，约 11-13 GiB/月）。

## 本地目录约定

```
E:/SystemCacheInfo/琉璃神社/20XX年合集/20XX年MM月合集/
```
- 2026 年已存：01-07 月（04-07 月通过 FDM 下载成功；07月 2026-09-05 下完）
- 合集发布滞后：N 月合集约在 N+1 月 15-16 号发布（如 6 月合集 7/16 发布，7 月合集 8/16 左右）

## 域名现状（2026-09-05 验证）

- **www.hacg.mov** ✅ 可用（主站，WordPress，路径 /wp/；合集文章页 URL 形如 `/wp/102860.html` 纯数字 ID，不再是 slug 模式）
- **www.hacg.me** ✅ 可用（同源镜像）
- hacg.ist ✅ 仍可参考（2026-08-09 验证为主站；神社域名常轮换，失效就用 hacg.mov/me）
- hacg.casa / hacg.la ⚠️ 曾是镜像（liulishe.ooo 公告 2026-04 提到 hacg.casa/wp）；liulishe.ooo 是地址公告页，域名轮换时去那找最新地址
- hacg.icu ❌ 已挂（旧域名，2026-06 时可用）
- www.liuli.in ❌ 已彻底失效：有 FingerprintJS 指纹跳转保护（curl 只能拿到跳转页），跟随 `tr_uuid&fp=` 跳转后落到 **ww38.liuli.in 停放页（HTTP 502）** → 域名已被注册商接管。别在 liuli.in 上浪费时间

## 快速检查"最新合集出了没"（用户每月例行）

1. **先查本地**：`ls "E:/SystemCacheInfo/琉璃神社/20XX年合集/"`，看已下到哪个月
2. **再查官网合集标签页**（比站内搜索更快，所有月度合集一页列全、按时间倒序）：
   ```
   https://www.hacg.mov/wp/tag/%e5%8a%a8%e7%94%bb%e5%90%88%e9%9b%86
   ```
   tag slug 是 `动画合集`（URL 编码 `%e5%8a%a8%e7%94%bb%e5%90%88%e9%9b%86`）。curl 抓这个页面，
   `grep -oE 'href="[^"]*"[^>]*>[^<]*合集'` 即可列出全部月合集标题+文章链接，无需浏览器。
   ⚠️ 直连 SSL 可能被掐（curl exit 35 / HTTP 000）——开 mihomo 代理后 curl 稳定 200。
3. **对照发布规律**：N 月合集约 N+1 月 15-16 号发布

   | 合集 | 发布日期 |
   |------|---------|
   | 2026年07月合集 | 2026-08 中下旬（09-05 已在站上，文章 102860） |
   | 2026年06月合集 | 2026-07-16 |
   | 2026年05月合集 | 2026-06-16 |
   | 2026年04月合集 | 2026-05-16 |
   | 2026年03月合集 | 2026-04-15 |
   | 2026年2月合集 | 2026-03-15 |
   | 2026年1月合集 | 2026-02-15 |

   发布前一周查不到是正常的，别下结论说"没出"——直接告诉用户预计日期即可。

## 查找流程

1. 站内搜索（curl 走代理）：
   ```
   https://www.hacg.mov/wp/?s=<URL编码关键词>
   ```
2. 打开合集文章页，URL 模式：`https://www.hacg.mov/wp/<文章ID>.html`（合集标签页的链接里有 ID）

3. **提取磁力 hash**：文章正文里唯一的 40 位 hex 就是整月合集包的 btih（无 `magnet:?xt=urn:btih:` 前缀，是裸 hash，页面里 `magnet:?xt=urn:btih:` 只出现在页脚模板文字里，别 grep 那个）。
   ```bash
   curl -s -m 15 -L "<文章URL>" -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" | \
     grep -oE "[0-9a-f]{40}" | sort -u
   ```
   验证方法：对比本地已有月份的页面 hash 与已知磁力（如 2026年03月页面 hash = `7cb8cbcf9b5c11bdffe70b960869406ae59d1163`，与历史记录一致），确认"页面唯一 hash = 整月包"。
   注意：页面可能包含单部作品的 hash 段落，但整月包 hash 通常就是页面唯一的 40-hex 串。

## 下载前：aria2c 探活 + 内容验证（新增推荐步骤，2026-09-05 实测）

FDM 解析磁力可能卡"请求信息中"很久（07月合集实测卡 10+ 分钟），别干等。下 13GiB 大包前先用
aria2c 探活并验证内容（~90s 内出结果，只下元数据不占流量）：

```bash
cd "$LOCALAPPDATA/Temp"
aria2c --bt-metadata-only=true --bt-save-metadata=true --bt-stop-timeout=80 --seed-time=0 \
  --bt-tracker="http://sukebei.tracker.wf:8888/announce,http://tracker.tasvideos.org:6969/announce,http://tracker.bt4g.com:2095/announce,http://tracker2.itzmx.com:6961/announce,udp://tracker.opentrackr.org:1337/announce,udp://tracker.openbittorrent.com:6969/announce" \
  "magnet:?xt=urn:btih:<40位hex>"
```

- 成功标志：`[MEMORY][METADATA] ... Download complete` + 存出 `<hash>.torrent`（CN≥1 即可，单 tracker 502 不影响——07月合集实测 sukebei.tracker.wf 报 502 但其余 tracker 兜底成功）
- 然后 `aria2c --show-files <hash>.torrent` 秒级列出种子内容：顶层目录名/文件清单/总大小
  - 07月合集实测：Name=`2026年07月合集`，Total Length=13GiB（14,493,322,778），含 `07月海报/ 08月预告/` 等，与 06 月结构一致 → 确认 hash 对应正确内容
- aria2c 也 `CN:0` 持续 90s+ = 死种，直接告诉用户换源/忽略
- **探活成功后：别等 FDM 慢慢解析磁力，直接喂 .torrent**（全流程 2026-09-05 07月合集验证成功，见 SKILL.md Pitfall #17）：
  1. 若 FDM 里已有同 hash 磁力任务卡"请求信息中"→ GUI 选中该行（Down 键）→ Delete 删掉 → Esc/Enter 关确认框 → 查 Softdeluxe 库确认 id 消失
  2. `terminal(background=true, ... ./fdm.exe 'C:/Users/Sun47/AppData/Local/Temp/<hash>.torrent')` — **任务创建即带齐 destinationPath+title，零"请求信息中"等待，直接开下**
- 下载完成后**字节求和验证**：python os.walk 求目录字节总和 == `aria2c --show-files` 的 Total Length（07月实测 14,493,322,778 零误差）
- **完成后更新本地记录**：`E:/SystemCacheInfo/琉璃神社/全部合集磁力链.txt` 追加该月 hash 行、更新"本地磁盘状态"段落（2026年: 01-07月 全齐）——用户靠这个文件追踪已下月份

## 下载：aria2c 直连大概率失败，用 FDM

**症状**：aria2c 能拿到元数据（`[MEMORY][METADATA]` 下载完成，总大小 11-13GiB 可见），连接大量 peer（CN:50-80），但 `DL:0B` 持续 —— GFW 掐 BT 数据流（同 IPZZ-276 案例）。

**有效方案：Free Download Manager（FDM）**

```bash
# FDM 是 GUI 程序：必须 background 启动（前台会卡到超时）
terminal(background=true, command="cd '/d/Program Files/Softdeluxe/Free Download Manager' && ./fdm.exe '<magnet>'" )
```

- **弹窗行为不固定，传完后截图确认**（2026-08-09 / 2026-09-05 实测）：
  - FDM **已在运行** + 记住了上次保存路径 → **不弹窗**，任务直接进队列自动开始下载，路径沿用上次（实测月合集落 `E:\SystemCacheInfo\琉璃神社\2026年合集\`，种子顶层自建 `2026年MM月合集\`）
  - FDM 未运行 + 有路径记忆 → 可能弹"添加下载"对话框，任务仍会用记住的路径自动开始
  - FDM 未运行 + 无路径记忆 → 弹窗等用户确认路径
- ⚠️ **磁力任务可能长期卡"请求信息中"（10+ 分钟）≠ 死种**——见 SKILL.md Pitfall #17 反向情形：用 aria2c 探活判定死活，别用 FDM 状态判定
- 月合集场景：保存路径应为 `E:\SystemCacheInfo\琉璃神社\2026年合集\`（FDM 记住的正是这个父目录，种子顶层 `2026年MM月合集` 自动建子目录，无需手动指定 MM月目录）
- 可截图确认 FDM 窗口状态（PowerShell CopyFromScreen 流程，见 windows-desktop-control 技能）

## ⚠️ 嵌套目录坑（2026-08 实战踩坑）

琉璃神社月合集种子的**顶层文件夹名与目标目录同名**（如 `2026年06月合集`）。

- **aria2c 下载时**：在目标目录内又建一个同名目录（`2026年06月合集/2026年06月合集/`），
  里面全是 **0 字节占位文件 + 空目录**（种子目录结构占位），下载失败后残留 → 24K 垃圾壳。
- **FDM 下载时**：检测到种子顶层文件夹与目标目录同名 → **直接平铺写入目标目录**，无嵌套。

**处理**：
1. 下载完成后必须验证目录结构（对照 04/05 月合集：`MM月海报/ 下月预告/ 简评.txt CHS/ CHT/ Fonts.zip RAW/ Subs.zip` 平铺）
2. 发现 `X月合集/X月合集/` 嵌套空壳：先确认 `find -type f -size +0` 无非空文件，再 `rm -rf` 嵌套层
3. 同时清理 `.aria2` 控制文件残留（`rm -f *.aria2`）

## FDM 数据库（Softdeluxe 版 v6.34，2026-09-05 确认）

**⚠️ 本机有两个 FDM 数据库，别用错！**

```
✅ 在用：C:/Users/Sun47/AppData/Local/Softdeluxe/Free Download Manager/db.sqlite
   （表 downloads，列：id/uuid/url/destinationPath/title/creationTime/finishedTime/flags）
❌ 废弃：C:/Users/Sun47/AppData/Local/Free Download Manager/fdm.sqlite
   （旧 ORG 版残留，2024-05 后不写，路径指向已删除的 D:/下载）
```

- **新任务在"请求信息中"阶段就落库**（id 递增可见），但 destinationPath/title 为 NULL，解析出元数据后填充——所以查库能确认"任务已进队列"，但内容/路径要等解析
- 已完成月合集任务：`destinationPath = E:/SystemCacheInfo/琉璃神社/2026年合集`（父目录），`title = 2026年MM月合集`，flags≈546314847
- 监控进度仍以文件系统为主：`ls` 目标目录看 `*.fdmdownload` 后缀临时文件（大小增长即下载中；完成后后缀消失 + `du -sh` ≈ 逻辑大小才算完，见 SKILL.md Pitfall #15）

## 备用思路（未验证，仅记录）

- 琉璃神社官方"不提供下载链接"（文章底部有免责声明），磁力 hash 是作者直接贴正文里的
- 评论区可能有补链，但官方警告"不要点击评论区不明链接"（防诈骗）

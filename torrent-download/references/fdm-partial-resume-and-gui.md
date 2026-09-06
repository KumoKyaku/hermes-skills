# FDM 断点续传 + GUI 诊断实战（2026-08-26 BOKO-009 会话）

场景：sukebei 找到 FHD 种子（3 seed，5.0GiB），FDM 下载 3 小时只完成 ~510MB/5GB，
监控脚本 180min 超时退出；用户手动把 `.fdmdownload` 改成 `.mp4` 后无法播放。

## 稀疏文件验证（判断"下完没"，最重要的一课）

FDM 预分配全量（稀疏文件）：`ls -la` 显示 5.37GB 逻辑大小，`du -sh` 只有 ~510MB 实数据。

```bash
du -sh "/e/SystemCacheInfo/琉璃神社/2026年合集/BOKO-009"   # 实数据（唯一可信）
ls -la 目录                                             # 逻辑大小（预分配，无意义）
```

文件内容验证（Python 读头/中/尾，无需 PIL）：
```python
import os
p = r'E:\...\hhd800.com@BOKO-009.mp4'
size = os.path.getsize(p)
with open(p, 'rb') as f:
    head = f.read(16); f.seek(size // 2); mid = f.read(16)
    f.seek(max(0, size - 16)); tail = f.read(16)
# head == b'\x00\x00\x00\x20ftyp'（MP4 正常），mid/tail 全 0 = 稀疏空洞 = 没下完
```

**判据：`.fdmdownload` 后缀消失 ≠ 完成**。任务被停止/出错时 FDM 也会去后缀。
monitor 脚本（wait_fdm_download.sh）报"DOWNLOAD COMPLETE"后必须再 `du -sh` 验证。

## 低速模式诊断（龟速元凶）

症状：任务"下载中"但速度 0~5KB/s，"剩余 6d22h"。
原因：FDM 工具栏"低速模式"（乌龟图标）被激活 → 全局限速。
确认：截 FDM 窗口图 → 视觉/像素分析乌龟图标高亮状态。
注意：按估算坐标点工具栏按钮易点偏（实测点中任务列表选中了别的任务）——点击后截图验证。

## 断点续传恢复（用户改后缀后）

1. `mv hhd800.com@BOKO-009.mp4 hhd800.com@BOKO-009.mp4.fdmdownload`（改回临时后缀）
2. `powershell.exe -NoProfile -Command "Stop-Process -Name fdm -Force"`
   （git-bash 的 `taskkill //F` 报"无效参数/选项"，PowerShell 兜底，同 mihomo 流程）
3. background 重启 fdm.exe → 任务从"文件丢失"恢复为"下载中"，断点（9%）保留

## 重复磁力 → "下载已存在"对话框

FDM 运行中重传同磁力：不静默入队，弹"下载已存在"（链接/路径/大小/添加时间），
Enter 确认默认按钮。若任务"文件丢失"，确认后仍不下载 → 先恢复文件再续传。

## GUI 自动化尝试（FDM 6 = Qt/QML）

- **UIA（System.Windows.Automation）**：能拿到窗口（Class: ApplicationWindow_QMLTYPE_96_QML_223），
  但递归找不到任何任务项——QML 自绘控件，UIA 不暴露内容。别在这条路上浪费时间。
- **WinRT OCR（Windows.Media.Ocr）**：PowerShell 可调通，识别出桌面图标但读不到 FDM
  窗口内文本（自绘小字）。脚本坑：`$line.Words[0]` 在 PS 里被解包成 Object[]，
  需 `@($line.Words)[0]`；`[System.WindowsRuntimeSystemExtensions]` 类型加载报错时
  改用反射 `[System.WindowsRuntimeSystemExtensions].GetMethods()` 找 AsTask。
- **像素分析**：hermes venv 的 PIL（_imaging ImportError）和 numpy（cp311/cp313 不匹配）
  都不可用 → 用纯 Python 解码 PNG（struct+zlib+手动 unfilter 0-4）+ 颜色分桶找按钮，
  见 `scripts/png_pixel_analyze.py`。分析结论要与窗口布局交叉验证（菜单栏/工具栏/任务列表
  的 y 范围要先确定，否则会把菜单文字当按钮）。

# 本机安装结果记录

记录于 2026-06-23，winget 重装 Everything + Python 后的实际状态。

## Everything

| 项目 | 值 |
|------|----|
| 版本 | 1.4.1.1032 |
| 安装方式 | `winget install voidtools.Everything -h --accept-source-agreements` |
| 主程序路径 | `C:\Program Files\Everything\Everything.exe` |
| es.exe 路径 | winget 链接目录 `%LOCALAPPDATA%\Microsoft\WinGet\Links\es.exe`（PATH 自动有） |
| es.exe 版本 | 1.1.0.37 |
| 安装包类型 | WIX (MSI) |
| Service | `everything.exe -install-service` 安装，Automatic，Running |
| 数据库路径 | `C:\ProgramData\Everything\`（ini 中 `db_location=...` 手动设置） |
| HTTP 服务 | `http_server_enabled=1`，端口 80（可用但非必需） |
| 索引结果 | ~3,510,210 文件（C+D+E+W 四盘） |
| es.exe 通信 | 需要 Everything GUI 窗口运行（IPC），否则 Error 8 |
| PATH 状态 | `C:\Program Files\Everything` 在用户 PATH 中 |

### 已知问题
- es.exe 如 hang 住会残留进程锁文件，需 `taskkill //F //IM es.exe` 才能清理目录
- 默认安装在 `C:\Program Files\Everything\`，Service 以 SYSTEM 运行，写不到 Program Files → **必须改 db_location**
- 卸载需要先 stop + delete service，再 winget uninstall，再手动 rmdir

## Python (仅保留两个)

| 项目 | 值 |
|------|----|
| 保留版本 | **Python 3.13.14**（winget）+ **Hermes venv 3.11.15**（运行依赖） |
| 已删除版本 | **3.14.3**（uv 管理, 288 MB）+ **2.7**（目录 + 注册表 MSI 残留）+ **uv shims**（`AppData\Local\Python\bin`） |
| Winget 路径 | `%LOCALAPPDATA%\Programs\Python\Python313\` |
| Hermes venv | `%HERMES_HOME%\hermes-agent\venv\`（Python 3.11.15，依赖 uv 管理的 3.11.15 源文件做标准库） |
| pip | Winget: 26.1.2（自带）；Hermes: uv pip |
| Python Launcher | `py.exe` 在 `C:\Windows\py.exe`，`py -3.13` 调 winget 版 |
| `python` 命令 | 在 Hermes 会话中指向 venv（3.11.15），新终端指向 winget（3.13.14） |

### 当前多版本一览（`py -0`）
```
 *               Active venv
 -V:3.13          Python 3.13 (64-bit)       ← winget，系统默认
 -V:Astral/CPython3.11.15  CPython 3.11.15   ← Hermes venv 依赖的源
```
(HKLM 2.7 注册表被 TrustedInstaller 锁死无法删除，但目录已删，无害。)

### PIP 配置
创建 `%APPDATA%\pip\pip.ini`：
```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

## Winget 包列表（相关）

| ID | 版本 | 安装类型 |
|----|------|---------|
| `voidtools.Everything` | 1.4.1.1032 | WIX |
| `voidtools.Everything.Cli` | 1.1.0.37 | - |
| `Python.Python.3.13` | 3.13.14 | MSI |

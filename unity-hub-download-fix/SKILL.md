---
name: unity-hub-download-fix
title: Unity Hub 下载失败修复（中国区）
description: Unity Hub 下载报错时，用 mihomo 台湾节点绕中国镜像+手动装安装包。
version: 1.0.0
tags: [unity, unity-hub, download, china, mirror, mihomo, proxy, akamai]
---

# Unity Hub 下载失败修复（中国区）

Unity Hub 下载编辑器报 `Validation Failed` 或 `Download failed: Response status was 404` 时使用。

## 根因（一句话）

Unity Hub 对**中国 IP** 强制走中国镜像 `download.unitychina.cn`（阿里云上海 OSS），而**新发布的版本（如 6000.5.8f1）中国镜像还没同步** → 返回 `NoSuchKey` 404 → Hub 报校验失败。走代理也没用，因为 Hub 压根不访问国际 CDN。

## 诊断步骤（快速确认根因）

```bash
# 1. 查版本下载信息（拿 hash 和大小）
curl -s "https://services.api.unity.com/unity/editor/release/v1/releases?version=<版本号如6000.5.8f1>" | python -c "
import json,sys
d=json.load(sys.stdin)
r=d['results'][0]
for dl in r['downloads']:
    if dl['platform']=='WINDOWS' and 'X86_64' in str(dl.get('architecture','')):
        print(dl['url']); print('size:', dl['downloadSize']['value'])
        print('md5:', __import__('base64').b64decode(dl['integrity'][4:]).hex())
"

# 2. 确认 CDN 重定向到中国镜像（直连时）
curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" "https://download.unity3d.com/download_unity/<hash>/Windows64EditorInstaller/UnitySetup64-<版本>.exe"
# 预期: 302 -> https://download.unitychina.cn/... （就是它！）

# 3. 确认中国镜像缺文件（返回 NoSuchKey XML = 阿里云 OSS 404）
curl -sL "https://download.unity3d.com/download_unity/<hash>/Windows64EditorInstaller/UnitySetup64-<版本>.exe" | head -c 200
# 预期: <Code>NoSuchKey</Code> 阿里云错误
```

## 解法 A：手动下载安装包（最稳，推荐）

关键：**必须走海外节点绕过 Akamai 的 GEO 重定向**。实测：香港节点仍被重定向到中国镜像，**台湾节点不被重定向**（直接 206）。

```bash
# 1. 启动 mihomo 代理
terminal(background=true, command="cd '<mihomo目录>' && ./mihomo.exe -f '<配置yaml绝对路径，正斜杠>'" )
# 路径示例: C:/Users/Sun47/OneDrive/翻墙/Clash_1777610321.yaml
# ⚠️ 路径必须用正斜杠！反斜杠会被 mihomo 当转义符（报 "Can't find config, create a initial config file"）

# 2. Clash 配置加规则（强制 unity3d.com 走台湾节点），先备份：
cp <配置yaml> <配置yaml>.bak.$(date +%H%M%S)
# 在 rules: 后插入（要放在 GEOIP CN 之前，用最前面的位置）：
#   - DOMAIN-SUFFIX,unity3d.com,🇹🇼 台湾4h
#   - DOMAIN-SUFFIX,unity.com,🇹🇼 台湾4h
# 改完重启 mihomo（kill + 重新 background 启动）

# 3. 后台下载完整安装包（3.8GB，约 8.7MB/s 需 6-7 分钟）
terminal(background=true, notify_on_complete=true, command="cd '<下载目录>' && curl -sL -x http://127.0.0.1:7890 --retry 3 -o 'UnitySetup64-<版本>.exe' 'https://download.unity3d.com/download_unity/<hash>/Windows64EditorInstaller/UnitySetup64-<版本>.exe'")

# 4. 验证 MD5（API 返回的 integrity 是 base64 的 md5）
python -c "
import hashlib,base64
h=hashlib.md5()
with open(r'<安装包路径>','rb') as f:
    for c in iter(lambda: f.read(8*1024*1024), b''): h.update(c)
print(h.hexdigest())  # 对比 API 解码的 md5
"

# 5. 静默安装（装到 Hub 的 Editor 目录，Hub 自动识别）
# GUI 启动（用户能看到安装向导，可能被 VS Installer 窗口挡住）：
powershell.exe -NoProfile -Command "Start-Process -FilePath '<安装包路径>' -Verb RunAs"
# 或静默装（不弹窗，需要先测目录可写，Program Files 需管理员）：
powershell.exe -NoProfile -Command "Start-Process -FilePath '<安装包路径>' -ArgumentList '/S','/D=C:\Program Files\Unity\Hub\Editor\<版本>' -Verb RunAs"
```

### 安装验证

```bash
powershell.exe -NoProfile -Command "(Get-Item 'C:\Program Files\Unity\Hub\Editor\<版本>\Editor\Unity.exe').VersionInfo | Select FileVersion,ProductVersion | Format-List"
# 预期: FileVersion=6000.5.8.6076383, ProductVersion=6000.5.8f1_5cb7df797b7d
# Hub 识别: 查 %APPDATA%\UnityHub\editors-v2.json 是否含版本号
```

## 解法 B：让 Hub 以后不走 unity.cn（改配置）

### 根因细节
Hub 启动时访问 `https://public-cdn.cloud.unity3d.com/config/`（代码里硬编码 `servicesConfigBaseUrl`），服务器按**来源 IP** 307 重定向到 `unitychina.cn` → 下发 `cloudConfig.json` 全是 `.cn` 域名 → 所有下载走中国镜像。

### 步骤
```bash
# 1. 备份并修改 cloudConfig.json（%APPDATA%\UnityHub\cloudConfig.json）
cp <cloudConfig.json> <cloudConfig.json>.bak
# 把 .cn 域名替换为国际域名：
#   core.cloud.unity.cn        -> core.cloud.unity3d.com
#   api.unity.cn               -> api.unity3d.com
#   license.unity.cn           -> license.unity3d.com
#   activation.unity.cn        -> activation.unity3d.com
#   id.unity.cn                -> id.unity3d.com
#   public-cdn.cloud.unitychina.cn -> public-cdn.cloud.unity3d.com
#   cdp.cloud.unity.cn         -> cdp.cloud.unity3d.com
#   packages-v2.unity.cn       -> packages-v2.unity.com
#   assetstore.u3d.cn          -> assetstore.unity.com
#   uos.u3dcloud.cn            -> uos.unity.cn（或删）

# 2. 注意：Hub 每次启动会重新拉取覆盖！配合 mihomo 规则（unity3d.com/unity.com 走台湾）+ 开系统代理时重启 Hub，服务器按台湾 IP 下发国际配置
```

### 系统代理开关（让 Hub 走 mihomo）
```bash
# 开：
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:7890" /f
# 关（用完必关，避免影响其他上网）：
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f
```

## 陷阱清单

1. **mihomo 配置路径必须正斜杠**：`-f "C:/Users/.../Clash_xxx.yaml"`，反斜杠报 "Can't find config" 或创建畸形目录
2. **香港节点也会被 Akamai 重定向**到中国镜像；**台湾节点不会**。节点选错 → 下载回来的是 457 字节 XML 错误而非安装包（MZ 头）
3. **下载成功后验证文件头**：`head -c 2 文件` 应为 `MZ`（exe 文件头），不是 `<?xml`
4. **安装器可能被 VS Installer 抢占**：Unity Hub 配置 `hubDisableVisualStudioDownload=False` 时会在后台自动装 Visual Studio，其窗口挡住 Unity 安装器。检查：`powershell Get-Process | Where {$_.Name -match 'setup'}`，有窗口标题 "Visual Studio Installer" 的就是它
5. **静默安装需要管理员**：Program Files 目录写入被拒时用 `-Verb RunAs`（弹 UAC）或让用户双击安装器
6. **安装包保留**：3.8GB 安装包放 E:\SystemCacheInfo\Others\ 留着，重装不用再翻墙
7. **mihomo 规则改动前必须备份** yaml
8. **用完关系统代理**，mihomo 进程也确认状态（有时会自动退出，代理变 000）

## 验证清单

- [ ] `download.unity3d.com` 直连返回 302 到 unitychina（确认根因）
- [ ] 走代理（台湾节点）+ 规则后下载返回 206 / 完整 MZ 文件
- [ ] MD5 与 API integrity 解码一致
- [ ] Unity.exe 版本号正确（6000.5.8f1_5cb7df797b7d）
- [ ] Hub editors-v2.json 识别到版本
- [ ] 系统代理已关闭

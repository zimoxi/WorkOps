# WorkOps

WorkOps 是一个面向个人、家庭实验室和小型办公环境的统一基础设施管理平台。

**One workspace for managing personal, homelab, and small office infrastructure.**

Backup Manager 是 WorkOps 的操作 / 备份模块，提供 NAS/restic 备份、ZFS dataset 迁移、Windows 盘符同步、云端同步，以及可选的 PVE/PBS 备份流程。

## 多语言支持

- **默认语言：中文**
- 支持切换 **English**
- 语言切换位于左侧边栏顶部，刷新后保持选择
- 多语言文案通过 `static/i18n.js` 字典维护
- 切换语言后界面立即更新，无需刷新页面

### 新增翻译

所有新增面向用户的文案必须通过 i18n 字典维护：

1. 在 `static/i18n.js` 的 `dict.zh` 和 `dict.en` 中添加 key
2. 在 JS 代码中使用 `WorkOps.t("key")` 或 `WorkOps.t("key", {param: value})`
3. 未翻译的字段回退到中文默认值

## 引导式备份流程

首页按照推荐顺序显示十个步骤：

1. 连接并发现存储。
2. 确认活动存储目标。
3. 规划或跳过 Dataset 迁移。
4. 配置 NAS 和 Restic。
5. 完成首次备份。
6. 完成恢复验证。
7. 配置自动计划与通知。
8. 配置或跳过 Windows 备份。
9. 配置或跳过云端异地备份。
10. 配置或跳过 PVE/PBS。

必要步骤按顺序提示，但不会锁住左侧菜单。Dataset、Windows、云端和 PVE/PBS 是可选步骤，可以填写原因后暂时跳过，并随时重新启用。

每个页面都会显示步骤位置、用途、开始前检查、字段示例、格式规则、安全提醒、完成标准和下一步入口。多条路径与规则统一每行填写一条；路径包含中文或空格时不需要手动添加 shell 引号。

## 自动存储建议

存储发现会从 ZFS Dataset 生成候选目标，并排除 `/`、`/tmp`、`/var`、`/etc`、`/root`、`/usr` 和 `/boot` 等系统挂载点，也会排除 `legacy`、`none` 和重复挂载点。

只有一个安全候选且尚未配置存储目标时，应用自动填写名称、类型、Pool 和挂载点，但不会自动保存。存在多个候选时，每行显示"设为存储目标"。使用者确认并点击"添加存储目标"后，应用才保存配置并重新读取一级文件夹。

## 字段填写规则

Windows 备份来源支持整个盘符或具体文件夹，每行一条：

```text
D:\
E:\
D:\财务资料
E:\照片\原图
```

NAS 目标使用 UNC 路径：

```text
\\10.0.0.10\数据备份\Windows-PC
```

Restic 包含路径、排除规则、恢复路径等多值字段同样每行填写一条。rclone remote 使用 `remote名称:/目录` 格式。PVE/PBS 页面中的 PBS Storage ID 指 PVE Datacenter → Storage 里的 ID，不是 datastore 文件路径。

## 工作流完成状态

应用尽量根据真实配置和成功任务自动判断状态：

- SSH 测试和存储发现均成功后，连接步骤完成。
- 活动存储目标确认后，存储步骤完成。
- Restic 仓库、密码文件和备份路径保存后，Restic 配置完成。
- 成功的 `restic backup` 和 `restic restore` 任务分别完成首次备份与恢复验证。
- 成功的云同步或 PBS 备份任务更新对应可选步骤。

跳过状态不代表功能已验证，只表示使用者有意暂不配置。

## CODEX_GUARD 验证边界

项目根目录 `CODEX_GUARD.md` 禁止 Codex 自动执行命令、SSH、Docker、备份、恢复、迁移和网络操作。代码修改完成后，以下检查由使用者手动执行：

```powershell
py -m unittest discover -s tests -v
py -m compileall -f backup_manager run.py
node --check static/workflow.js
node --check static/app.js
node --check static/i18n.js
```

浏览器需要手动检查桌面和手机宽度下的流程清单、自动填写、字段说明、跳过/重新启用、下一步导航、危险确认框和页面横向溢出。

## 当前能力

- 存储发现：读取 `zpool list`、`zfs list`、`df -h`，并显示挂载点一级文件夹。
- NAS/restic：配置仓库、备份集、查看快照、执行备份、检查仓库、按策略 prune、恢复到指定目录。
- Dataset 迁移助手：创建同 pool 临时迁移目录，生成 `rsync -aHAX` 迁移命令。
- Windows 备份：为 D/E 等盘符生成 `robocopy` 命令。
- 云端同步：通过 `rclone sync` 同步加密后的 restic 仓库。
- PVE/PBS 附加模块：读取 VM/CT/PVE storage，生成 `vzdump` 到 PBS 的备份命令。
- 危险弹窗：恢复、prune、dataset 迁移、云同步等高风险操作必须输入确认文字。
- 白名单命令：后端不提供任意 shell 输入。

## Windows 本地测试

在 Windows 下不需要 Docker：

```powershell
cd C:\Users\54327\Documents\设计LOGO动图\gensol-backup-manager
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
py run.py --host 127.0.0.1 --port 8099
```

然后打开：

```text
http://127.0.0.1:8099
```

默认是 `mock` 模式，不会真正执行 ZFS、restic、PVE 或 rclone 命令。

## OMV Docker 部署

在 OMV 上进入项目目录后运行：

```bash
docker compose up -d --build
```

访问：

```text
http://<OMV_IP>:8099
```

### 从 Backup Manager 升级

旧版本服务名为 `backup-manager`，新版本为 `workops`。需要先停掉旧容器再重新启动：

```bash
docker compose down        # 停止旧 backup-manager 容器
docker compose up -d --build  # 启动新 workops 容器
```

如果旧容器是手动 `docker run` 启动的：

```bash
docker stop backup-manager
docker rm backup-manager
docker compose up -d --build
```

数据目录 `./data` 无需迁移，新旧版本共用同一份 `config.json` 和 `jobs.jsonl`。

容器默认不使用：

```text
privileged
docker.sock
OMV 插件
ZFS 内核模块
```

如果要让容器管理 OMV/PVE 宿主机命令，请在页面里选择 `ssh` 执行模式。使用私钥或已有 SSH 配置时，将 SSH 目录只读挂载进容器：

```yaml
volumes:
  - ./data:/app/data
  - /root/.ssh:/root/.ssh:ro
```

## 执行模式

`mock`：本地测试模式，只显示命令预览，不执行真实操作。

`local`：在当前运行应用的 Linux 主机执行白名单命令。

`ssh`：通过 SSH 到 OMV 或 PVE 主机执行白名单命令。适合 Docker 控制台模式。

## SSH 认证方式

应用让管理员选择目标系统原有的连接方式，不会强制改用某一种认证。

### 已有 SSH 配置 / Agent

使用 OpenSSH 默认密钥、`~/.ssh/config` 中的 Host 别名或 SSH Agent。容器使用配置文件时需要只读挂载 `.ssh` 目录；使用 Agent 时还要把 Agent socket 挂载到 `/ssh-agent`，并设置：

```yaml
environment:
  SSH_AUTH_SOCK: /ssh-agent
volumes:
  - ${SSH_AUTH_SOCK}:/ssh-agent
```

### SSH 私钥

将私钥和 `known_hosts` 只读挂载到容器，然后在页面填写容器内路径，例如：

```text
/root/.ssh/id_ed25519
```

应用只保存路径，不复制或读取私钥内容。

### SSH 密码

Windows 和 Docker 的密码模式都使用 Paramiko，不再依赖 `sshpass`。密码只保存在当前网页和请求内存中，不进入命令行、配置文件或任务日志；刷新网页后密码会清除。

Windows 首次使用前安装依赖：

```powershell
py -m pip install -r requirements.txt
```

### 主机指纹

应用不会关闭 SSH 主机指纹检查。首次连接前应在 OMV/PVE 控制台核对主机指纹，再将目标写入应用可读取的 `known_hosts`。如果出现主机密钥发生变化的提示，应先调查目标系统是否重装或 IP 是否被其他机器占用，不要直接绕过检查。

Windows 可以先手动建立并核对记录：

```powershell
ssh root@10.0.0.10 -p 22
```

核对服务器显示的指纹后输入 `yes`。即使之后密码输入失败，已确认的主机密钥仍会写入 `C:\Users\<用户名>\.ssh\known_hosts`。

保存连接设置后，先点击"测试 SSH 连接"。连接成功后再执行"读取系统信息"或备份任务。

## 推荐恢复位置

不要恢复到：

```text
/tmp
/
/var
/etc
/root
/usr
/boot
```

推荐恢复到：

```text
<pool_mountpoint>/restore-test
/mnt/usb-restore
另一台大容量机器的挂载目录
```

## Dataset 迁移原则

如果只有 pool 里有足够空间，临时迁移目录也应该建在同一个 pool 里：

```text
<pool_mountpoint>/_migration_YYYYMMDD
```

迁移流程建议：

```bash
mkdir -p /pool/_migration_YYYYMMDD
mv /pool/目录 /pool/_migration_YYYYMMDD/目录.old
zfs create pool/目录
rsync -aHAX --numeric-ids --info=progress2 /pool/_migration_YYYYMMDD/目录.old/ /pool/目录/
```

确认无误前不要删除 `.old`。

## PVE/PBS 附加模块

这个模块必须在 PVE 宿主机侧执行，不要放在 OMV 虚拟机里运行真实备份命令。

建议流程：

1. 在 PVE 中接入 PBS storage。
2. 在应用中选择 `ssh` 到 PVE 宿主机。
3. 读取 `qm list`、`pct list`、`pvesm status`。
4. 选择 VM/CT，执行 `vzdump <vmid> --storage <pbs-storage> --mode snapshot`。
5. 在 PBS/PVE 中做 verify。
6. 升级 PVE 前，把关键 VM/CT 恢复到临时 VMID/CTID 做恢复演练。

PBS 备份不是"指定成某个 PVE 版本格式"。更可靠的做法是保存宿主机配置、记录 storage/bridge/直通设备，并在目标 PVE 版本上做恢复演练。

## 云端同步

应用通过 `rclone` 接入云端服务商。建议只同步加密后的 restic 仓库：

```text
<pool_mountpoint>/_cloud_restic/<repo>
```

不要直接上传明文业务文件。

账号密码、OAuth token 建议交给 `rclone config` 管理。应用只保存 remote 名称和同步路径。

## 测试

```bash
python -m unittest discover -s tests -v
python -m compileall backup_manager run.py
```

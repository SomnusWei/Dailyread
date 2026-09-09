# 每日阅读备份助手（Windows）

把部署服务器上的数据安全备份到**本地目录或 NAS 共享**的小工具（PyQt6 + paramiko）。

备份源为每日自动生成的完整数据包，本工具负责 **拉取 + 完整性校验 + 落盘 + 定期执行 + 保留清理**。全链路：

```
服务器（47.95.205.216 /opt/dailyread-server）
  │  每日 03:10 cron 执行 scripts/backup.sh：
  │    mysqldump --single-transaction 热备全库(含建库语句)
  │    + public/ uploads/ schema.sql 打包
  │    产物 backups/backup-<YYYYmmdd-HHMM>/
  │       ├─ db-<ts>.sql       数据库逻辑备份
  │       ├─ site-<ts>.tar.gz  站点数据
  │       ├─ sha256.txt        校验清单
  │       └─ backup.log        出包日志
  ▼  Windows 备份助手（本工具）SSH/SFTP 拉取
本地 / NAS 共享（如 \\NAS\DailyReadBackup\backup-<ts>\…）
```

服务器端 `scripts/backup.sh` + `scripts/db_env.js` 已随仓库提供并部署到位（cron 已配 03:10；凭据经 dotenv 从应用 `.env` 读取，脚本内不落密码）。服务器保留最近 30 天，本机侧保留天数可在界面设置。

## 运行 / 打包

```bash
pip install -r requirements.txt      # PyQt6 / paramiko
python backup_assistant.py           # 界面运行（双击 run.bat 亦可）
python -m PyInstaller --clean --noconfirm app.spec   # 打包 → dist\每日阅读备份助手.exe
```

## 使用步骤

1. **备份目标**（“立即备份”页）：填本地路径或 NAS 共享（`\\NAS\DailyReadBackup`）。NAS 目录请先在本机“资源管理器”登录一次并**勾选记住凭据**，计划任务才能以本机身份写入。
2. **立即备份**：默认 SSH 信息已指向部署机（私钥 `~\.ssh\serverssh`，可换）。点「立即备份」= 先远程触发服务器出包，再拉取；点「仅拉取服务器最新包」= 不触发、直接拉最新已有包。
3. **定期自动**：选频率与时间 → 「注册/更新计划任务」（任务名 `DailyReadBackupAuto`）。可选“错过开机尽快补跑”，关机错过也会在下次开机自动补一次。执行体为 `每日阅读备份助手.exe --auto` 静默模式。

## 数据与说明

- 配置文件：`%APPDATA%\DailyReadBackup\config.json`
- 执行日志：`%APPDATA%\DailyReadBackup\logs\YYYY-MM.log`（界面同步显示）
- 自动跳过：目标已存在同名备份包且 SHA-256 一致时不重复下载
- 历史页可对任意备份包做 **SHA-256 校验 / 删除**；「恢复指引」内含数据库导入与站点解压步骤
- 源端与目标端各自独立按“目录名时间戳”保留 N 天（默认 30），互不影响

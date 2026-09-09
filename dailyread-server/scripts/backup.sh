#!/usr/bin/env bash
# =============================================================
# DailyRead 服务器数据备份脚本
#
# 产物目录：/opt/dailyread-server/backups/backup-<YYYYmmdd-HHMM>/
#   db-<ts>.sql        MySQL 全量逻辑备份（--single-transaction 在线热备，含建库语句）
#   site-<ts>.tar.gz   站点数据（public/ uploads/ schema.sql，排除依赖与历史备份）
#   sha256.txt         db / site 的 SHA-256 校验清单
#   backup.log         本次备份执行记录
#
# 保留策略：默认仅保留最近 30 天的备份目录，更早自动清理。
# 数据库凭据：由 scripts/db_env.js 经 dotenv 读取应用 .env 后注入环境变量，
#             脚本不硬编码、不回显密码。
# =============================================================
set -euo pipefail

APP_DIR=/opt/dailyread-server
BACKUP_ROOT="$APP_DIR/backups"
KEEP_DAYS="${KEEP_DAYS:-30}"
TS="$(date +%Y%m%d-%H%M)"
OUT="$BACKUP_ROOT/backup-$TS"
LOG="$OUT/backup.log"

mkdir -p "$OUT"
echo "[$(date '+%F %T')] 开始备份 -> $OUT" | tee -a "$LOG"

# ---- 1. 读取数据库配置（应用 .env -> dotenv，与 Node 服务解析一致）----
if ! eval "$(node "$APP_DIR/scripts/db_env.js" 2>>"$LOG")"; then
  echo "[$(date '+%F %T')] 读取 .env 数据库配置失败，终止" | tee -a "$LOG"
  exit 1
fi

# ---- 2. MySQL 全量备份（热备，不锁表）----
export MYSQL_PWD="$DB_PASSWORD"
if mysqldump -h"${DB_HOST:-localhost}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" \
      --single-transaction --quick --routines --triggers --hex-blob \
      --databases "${DB_NAME:-dailyread_db}" > "$OUT/db-$TS.sql" 2>>"$LOG"; then
  unset MYSQL_PWD
  echo "[$(date '+%F %T')] 数据库备份完成: $(du -h "$OUT/db-$TS.sql" | cut -f1)" | tee -a "$LOG"
else
  unset MYSQL_PWD
  echo "[$(date '+%F %T')] mysqldump 失败，详见 backup.log" | tee -a "$LOG"
  exit 1
fi

# ---- 3. 站点数据打包（排除 node_modules / 历史备份 / 旧单包）----
if ! tar -czf "$OUT/site-$TS.tar.gz" -C "$APP_DIR" \
      --exclude='node_modules' --exclude='backups' --exclude='backup' \
      public uploads schema.sql 2>>"$LOG"; then
  echo "[$(date '+%F %T')] 站点数据打包失败" | tee -a "$LOG"
  exit 1
fi
echo "[$(date '+%F %T')] 站点数据打包完成: $(du -h "$OUT/site-$TS.tar.gz" | cut -f1)" | tee -a "$LOG"

# ---- 4. 生成 SHA-256 校验清单 ----
(cd "$OUT" && sha256sum db-*.sql site-*.tar.gz > sha256.txt)
echo "[$(date '+%F %T')] 已生成 sha256.txt" | tee -a "$LOG"

# ---- 5. 清理超过保留期的历史备份 ----
OLD="$(find "$BACKUP_ROOT" -maxdepth 1 -type d -name 'backup-*' -mtime +"$KEEP_DAYS" -print)"
if [ -n "$OLD" ]; then
  echo "$OLD" | while IFS= read -r d; do
    rm -rf "$d"
    echo "[$(date '+%F %T')] 清理过期备份: $d"
  done | tee -a "$LOG"
else
  echo "[$(date '+%F %T')] 无过期备份需清理" | tee -a "$LOG"
fi

echo "[$(date '+%F %T')] 备份完成" | tee -a "$LOG"

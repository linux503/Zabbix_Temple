#!/bin/bash
# Zabbix MySQL 监控脚本
# 用法: mysql_status.sh <metric>
# 对应 UserParameter: mysql.status[*]
# 凭据可通过环境变量或默认配置文件提供:
#   MYSQL_USER / MYSQL_PASSWORD / MYSQL_HOST / MYSQL_PORT
#   或 /etc/zabbix/.my.cnf

METRIC="$1"
MYSQL_BIN="${MYSQL_BIN:-mysql}"
MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-zabbix}"
MYSQL_CNF="${MYSQL_CNF:-/etc/zabbix/.my.cnf}"

if [[ -z "$METRIC" ]]; then
  echo "ZBX_NOTSUPPORTED: missing metric"
  exit 1
fi

MYSQL_ARGS=()
if [[ -f "$MYSQL_CNF" ]]; then
  MYSQL_ARGS=(--defaults-extra-file="$MYSQL_CNF")
else
  MYSQL_ARGS=(-h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER")
  if [[ -n "${MYSQL_PASSWORD:-}" ]]; then
    MYSQL_ARGS+=(-p"$MYSQL_PASSWORD")
  fi
fi

case "$METRIC" in
  Ping)
    if "$MYSQL_BIN" "${MYSQL_ARGS[@]}" -N -e "SELECT 1" >/dev/null 2>&1; then
      echo 1
    else
      echo 0
    fi
    ;;
  Version)
    "$MYSQL_BIN" "${MYSQL_ARGS[@]}" -N -e "SELECT VERSION();" 2>/dev/null || echo "ZBX_NOTSUPPORTED"
    ;;
  Slave_status|Slave_running)
    # 1=运行中/有从库状态，0=否
    out=$("$MYSQL_BIN" "${MYSQL_ARGS[@]}" -e "SHOW SLAVE STATUS\G" 2>/dev/null)
    if [[ -z "$out" ]]; then
      echo 0
    else
      io=$(echo "$out" | awk '/Slave_IO_Running:/{print $2}')
      sql=$(echo "$out" | awk '/Slave_SQL_Running:/{print $2}')
      if [[ "$io" == "Yes" && "$sql" == "Yes" ]]; then
        echo 1
      else
        echo 0
      fi
    fi
    ;;
  '*')
    echo "ZBX_NOTSUPPORTED"
    ;;
  *)
    value=$("$MYSQL_BIN" "${MYSQL_ARGS[@]}" -N -e "SHOW GLOBAL STATUS LIKE '${METRIC}';" 2>/dev/null | awk '{print $2}')
    if [[ -z "$value" ]]; then
      # 尝试 GLOBAL VARIABLES（如 max_connections）
      value=$("$MYSQL_BIN" "${MYSQL_ARGS[@]}" -N -e "SHOW GLOBAL VARIABLES LIKE '${METRIC}';" 2>/dev/null | awk '{print $2}')
    fi
    if [[ -z "$value" ]]; then
      echo "ZBX_NOTSUPPORTED: $METRIC"
      exit 1
    fi
    echo "$value"
    ;;
esac

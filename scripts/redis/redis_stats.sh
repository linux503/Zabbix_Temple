#!/bin/bash
# Zabbix Redis 监控脚本
# 用法: redis_stats.sh <port> <metric>
# 对应 UserParameter: redis_stats[*]

PORT="${1:-6379}"
METRIC="$2"
REDIS_CLI="${REDIS_CLI:-redis-cli}"
REDIS_PASS="${REDIS_PASSWORD:-}"

if [[ -z "$METRIC" ]]; then
  echo "ZBX_NOTSUPPORTED: missing metric"
  exit 1
fi

# 模板里 used_memory 写成了 used_memory:，这里兼容两种写法
METRIC="${METRIC%:}"

AUTH_ARGS=()
if [[ -n "$REDIS_PASS" ]]; then
  AUTH_ARGS=(-a "$REDIS_PASS")
fi

INFO="$("$REDIS_CLI" -p "$PORT" "${AUTH_ARGS[@]}" INFO 2>/dev/null)"
if [[ -z "$INFO" ]]; then
  echo "ZBX_NOTSUPPORTED: redis unreachable on port $PORT"
  exit 1
fi

case "$METRIC" in
  role|redis_version)
    value=$(echo "$INFO" | awk -F: -v k="$METRIC" 'tolower($1)==tolower(k){gsub(/\r/,"",$2); print $2; exit}')
    ;;
  *)
    value=$(echo "$INFO" | awk -F: -v k="$METRIC" 'tolower($1)==tolower(k){gsub(/\r/,"",$2); print $2; exit}')
    ;;
esac

if [[ -z "$value" ]]; then
  echo "ZBX_NOTSUPPORTED: metric $METRIC not found"
  exit 1
fi

echo "$value"

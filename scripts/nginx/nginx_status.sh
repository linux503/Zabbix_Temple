#!/bin/bash
# Zabbix Nginx stub_status 监控脚本
# 用法: nginx_status.sh <metric> <status_url>
# 对应 UserParameter: nginx[*]
# 示例 URL: http://127.0.0.1/nginx_status

METRIC="$1"
URL="${2:-http://127.0.0.1/nginx_status}"
CURL_BIN="${CURL_BIN:-curl}"

if [[ -z "$METRIC" ]]; then
  echo "ZBX_NOTSUPPORTED: missing metric"
  exit 1
fi

BODY=$("$CURL_BIN" -s --max-time 5 "$URL" 2>/dev/null)
if [[ -z "$BODY" ]]; then
  echo "ZBX_NOTSUPPORTED: cannot fetch $URL"
  exit 1
fi

# stub_status 典型输出:
# Active connections: 3
# server accepts handled requests
#  120 120 360
# Reading: 0 Writing: 1 Waiting: 2

active=$(echo "$BODY" | awk '/Active connections/{print $3}')
reading=$(echo "$BODY" | awk '/Reading/{print $2}')
writing=$(echo "$BODY" | awk '/Writing/{print $4}')
waiting=$(echo "$BODY" | awk '/Waiting/{print $6}')
accepted=$(echo "$BODY" | awk 'NR==3{print $1}')
handled=$(echo "$BODY" | awk 'NR==3{print $2}')
requests=$(echo "$BODY" | awk 'NR==3{print $3}')

case "$METRIC" in
  active_connections) echo "${active:-0}" ;;
  reading)            echo "${reading:-0}" ;;
  writing)            echo "${writing:-0}" ;;
  waiting)            echo "${waiting:-0}" ;;
  accepted_connections) echo "${accepted:-0}" ;;
  handled_connections)  echo "${handled:-0}" ;;
  handled_requests)     echo "${requests:-0}" ;;
  *)
    echo "ZBX_NOTSUPPORTED: unknown metric $METRIC"
    exit 1
    ;;
esac

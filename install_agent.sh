#!/bin/bash
# 将被监控机所需的脚本与 UserParameter 安装到本机
# 用法: sudo ./install_agent.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_DST="${SCRIPTS_DST:-/etc/zabbix/scripts}"
CONF_DST="${CONF_DST:-/etc/zabbix/zabbix_agentd.d}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请使用 root 执行: sudo $0"
  exit 1
fi

mkdir -p "$SCRIPTS_DST" "$CONF_DST"
cp -a "$ROOT/scripts/." "$SCRIPTS_DST/"
cp -a "$ROOT/conf/." "$CONF_DST/"
chmod +x "$SCRIPTS_DST"/redis/*.sh "$SCRIPTS_DST"/mysql/*.sh "$SCRIPTS_DST"/nginx/*.sh
chmod +x "$SCRIPTS_DST"/mongodb/*.py 2>/dev/null || true

echo "已安装:"
echo "  脚本 -> $SCRIPTS_DST"
echo "  配置 -> $CONF_DST"
echo
echo "请确认 /etc/zabbix/zabbix_agentd.conf 含有:"
echo "  Include=$CONF_DST/*.conf"
echo
if command -v systemctl >/dev/null 2>&1; then
  systemctl restart zabbix-agent 2>/dev/null \
    || systemctl restart zabbix-agent2 2>/dev/null \
    || echo "请手动重启 zabbix-agent / zabbix-agent2"
  echo "Agent 已尝试重启。"
else
  echo "请手动重启 zabbix-agent。"
fi

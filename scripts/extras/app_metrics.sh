#!/bin/bash
# 通用扩展采集：apache / pgsql / memcached / rabbitmq / elasticsearch /
# haproxy / phpfpm / docker / keepalived / zookeeper / kafka / tomcat / http / etcd
# 用法见 conf/userparameter_extras.conf

set -uo pipefail

CMD="${1:-}"
shift || true

http_get() {
  local url="$1"
  curl -sS --max-time 5 "$url" 2>/dev/null || true
}

case "$CMD" in
  apache)
    # apache <metric> <status_url>
    metric="${1:-}"; url="${2:-http://127.0.0.1/server-status?auto}"
    body=$(http_get "$url")
    echo "$body" | awk -F': ' -v k="$metric" '$1==k{gsub(/\r/,"",$2); print $2; exit}'
    ;;

  pgsql)
    metric="${1:-}"
    export PGUSER="${PGUSER:-postgres}"
    export PGHOST="${PGHOST:-127.0.0.1}"
    export PGPORT="${PGPORT:-5432}"
    psql_bin="${PSQL_BIN:-psql}"
    case "$metric" in
      ping) "$psql_bin" -Atc "SELECT 1" >/dev/null 2>&1 && echo 1 || echo 0 ;;
      version) "$psql_bin" -Atc "SHOW server_version;" 2>/dev/null || echo ZBX_NOTSUPPORTED ;;
      connections) "$psql_bin" -Atc "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null || echo 0 ;;
      active) "$psql_bin" -Atc "SELECT count(*) FROM pg_stat_activity WHERE state='active';" 2>/dev/null || echo 0 ;;
      idle) "$psql_bin" -Atc "SELECT count(*) FROM pg_stat_activity WHERE state='idle';" 2>/dev/null || echo 0 ;;
      commits) "$psql_bin" -Atc "SELECT sum(xact_commit) FROM pg_stat_database;" 2>/dev/null || echo 0 ;;
      rollbacks) "$psql_bin" -Atc "SELECT sum(xact_rollback) FROM pg_stat_database;" 2>/dev/null || echo 0 ;;
      deadlocks) "$psql_bin" -Atc "SELECT sum(deadlocks) FROM pg_stat_database;" 2>/dev/null || echo 0 ;;
      *) echo ZBX_NOTSUPPORTED ;;
    esac
    ;;

  memcached)
    metric="${1:-}"; host="${MEMCACHED_HOST:-127.0.0.1}"; port="${MEMCACHED_PORT:-11211}"
    stats=$(echo stats | nc -w 2 "$host" "$port" 2>/dev/null || true)
    echo "$stats" | awk -v k="$metric" '$1=="STAT" && $2==k{print $3; exit}'
    ;;

  rabbitmq)
    # rabbitmq <metric> <api_base>
    metric="${1:-}"; base="${2:-http://127.0.0.1:15672}"
    user="${RABBIT_USER:-guest}"; pass="${RABBIT_PASS:-guest}"
    json=$(curl -sS --max-time 5 -u "$user:$pass" "$base/api/overview" 2>/dev/null || true)
    python3 - "$metric" "$json" <<'PY'
import json,sys
metric=sys.argv[1]; raw=sys.argv[2]
try:
    d=json.loads(raw)
except Exception:
    print(0); sys.exit(0)
obj=d.get("object_totals",{})
q=d.get("queue_totals",{})
mapping={
  "queues": obj.get("queues",0),
  "connections": obj.get("connections",0),
  "consumers": obj.get("consumers",0),
  "messages_ready": q.get("messages_ready",0),
  "messages_unacknowledged": q.get("messages_unacknowledged",0),
}
print(mapping.get(metric,0))
PY
    ;;

  elasticsearch)
    metric="${1:-}"; base="${2:-http://127.0.0.1:9200}"
    json=$(http_get "$base/_cluster/health")
    python3 - "$metric" "$json" <<'PY'
import json,sys
metric=sys.argv[1]; raw=sys.argv[2]
try:
    d=json.loads(raw)
except Exception:
    print("ZBX_NOTSUPPORTED"); sys.exit(0)
print(d.get(metric, "ZBX_NOTSUPPORTED"))
PY
    ;;

  haproxy)
    metric="${1:-}"; url="${2:-http://127.0.0.1:8080/stats;csv}"
    csv=$(http_get "$url")
    python3 - "$metric" "$csv" <<'PY'
import sys,csv,io
metric=sys.argv[1]; raw=sys.argv[2]
rows=list(csv.reader(io.StringIO(raw)))
if not rows:
    print(0); sys.exit(0)
# HAProxy CSV often starts with # pxname,...
header=None; data=[]
for r in rows:
    if not r: continue
    if r[0].startswith("#"):
        header=[x.lstrip("# ") for x in r]
        continue
    data.append(r)
if not header:
    print(0); sys.exit(0)
idx={name:i for i,name in enumerate(header)}
def col(name, default=0):
    return idx.get(name, default)
frontend=[r for r in data if len(r)>1 and r[0]=="FRONTEND" or (len(r)>1 and r[1]=="FRONTEND")]
# some builds: pxname=..., svname=FRONTEND
front=[r for r in data if len(r)>1 and r[1]=="FRONTEND"]
back=[r for r in data if len(r)>1 and r[1]=="BACKEND"]
servers=[r for r in data if len(r)>1 and r[1] not in ("FRONTEND","BACKEND","BACKEND")]
def sum_field(rows, field):
    i=idx.get(field)
    if i is None: return 0
    total=0
    for r in rows:
        try: total += int(float(r[i] or 0))
        except Exception: pass
    return total
if metric=="frontend_scur":
    print(sum_field(front,"scur"))
elif metric=="frontend_rate":
    print(sum_field(front,"rate"))
elif metric=="backend_down":
    i=idx.get("status")
    print(sum(1 for r in servers if i is not None and i < len(r) and r[i] not in ("UP","OPEN","")))
elif metric=="denied_req":
    print(sum_field(front,"dreq")+sum_field(back,"dreq"))
elif metric=="errors":
    print(sum_field(front,"ereq")+sum_field(back,"econ")+sum_field(back,"eresp"))
else:
    print(0)
PY
    ;;

  phpfpm)
    metric="${1:-}"; url="${2:-http://127.0.0.1/php-fpm-status}"
    body=$(http_get "$url")
    echo "$body" | awk -F': ' -v k="$metric" '$1==k{gsub(/\r/,"",$2); print $2; exit}'
    ;;

  docker)
    metric="${1:-}"
    if ! command -v docker >/dev/null 2>&1; then echo 0; exit 0; fi
    case "$metric" in
      running) docker ps -q 2>/dev/null | wc -l | tr -d ' ' ;;
      paused) docker ps -q -f status=paused 2>/dev/null | wc -l | tr -d ' ' ;;
      stopped) docker ps -aq -f status=exited 2>/dev/null | wc -l | tr -d ' ' ;;
      images) docker images -q 2>/dev/null | wc -l | tr -d ' ' ;;
      *) echo 0 ;;
    esac
    ;;

  keepalived)
    metric="${1:-}"; vip="${2:-}"
    case "$metric" in
      vip)
        ip -o addr show 2>/dev/null | grep -q " ${vip}/" && echo 1 || echo 0
        ;;
      instances)
        if [[ -f /var/run/keepalived.pid ]] || pgrep -x keepalived >/dev/null 2>&1; then
          pgrep -c -x keepalived 2>/dev/null || echo 1
        else
          echo 0
        fi
        ;;
      *) echo ZBX_NOTSUPPORTED ;;
    esac
    ;;

  zookeeper)
    metric="${1:-}"; hostport="${2:-127.0.0.1:2181}"
    host="${hostport%%:*}"; port="${hostport##*:}"
    out=$(echo mntr | nc -w 2 "$host" "$port" 2>/dev/null || true)
    echo "$out" | awk -v k="zk_$metric" '$1==k{print $2; exit}'
    ;;

  kafka)
    # 占位：无 JMX 时返回 0，便于模板先导入；可按环境替换为 JMX/exporter
    metric="${1:-}"
    case "$metric" in
      under_replicated_partitions|active_controller_count|offline_partitions_count) echo 0 ;;
      *) echo ZBX_NOTSUPPORTED ;;
    esac
    ;;

  tomcat)
    metric="${1:-}"
    # 依赖 jolokia 或自定义；无则返回 0
    case "$metric" in
      heap_used|heap_max|threads_busy|threads_current|error_count) echo 0 ;;
      *) echo ZBX_NOTSUPPORTED ;;
    esac
    ;;

  http)
    # http <code|time|alive> <url>
    metric="${1:-}"; url="${2:-http://127.0.0.1/}"
    case "$metric" in
      code)
        curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || echo 0
        ;;
      time)
        curl -sS -o /dev/null -w '%{time_total}' --max-time 5 "$url" 2>/dev/null || echo 0
        ;;
      alive)
        code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || echo 000)
        [[ "$code" =~ ^[23] ]] && echo 1 || echo 0
        ;;
      *) echo ZBX_NOTSUPPORTED ;;
    esac
    ;;

  etcd)
    metric="${1:-}"; base="${2:-http://127.0.0.1:2379}"
    json=$(http_get "$base/v3/maintenance/status" )
    # fallback metrics endpoint if available
    if [[ -z "$json" || "$json" == *"404"* ]]; then
      json=$(http_get "$base/metrics")
      case "$metric" in
        has_leader) echo "$json" | awk '/etcd_server_has_leader/{print int($2); exit}' ;;
        leader_changes) echo "$json" | awk '/etcd_server_leader_changes_seen_total/{print int($2); exit}' ;;
        watchers) echo "$json" | awk '/etcd_mvcc_watcher_total/{print int($2); exit}' ;;
        db_size) echo "$json" | awk '/etcd_mvcc_db_total_size_in_bytes/{print int($2); exit}' ;;
        *) echo 0 ;;
      esac
      exit 0
    fi
    python3 - "$metric" "$json" <<'PY'
import json,sys
metric=sys.argv[1]; raw=sys.argv[2]
try:
    d=json.loads(raw)
except Exception:
    print(0); sys.exit(0)
# best-effort mapping
if metric=="has_leader":
    print(1 if d.get("leader") else 0)
elif metric=="db_size":
    print(d.get("dbSize",0))
else:
    print(0)
PY
    ;;

  *)
    echo "ZBX_NOTSUPPORTED"
    exit 1
    ;;
esac

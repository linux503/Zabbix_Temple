# Zabbix_Temple

Zabbix 监控模板仓库：**20 套精简模板** + 经典完整模板 + Agent 脚本 + **50 个主机群组**。

| 项目 | 说明 |
|------|------|
| 推荐导入 | `templates/` 下 **20 套** Basic 模板（统一 Zabbix 3.0 XML） |
| 经典完整版 | 根目录旧 XML（MySQL / MongoDB / Redis / Nginx，监控项更全） |
| Agent 脚本 | `scripts/` + `conf/`，可用 `install_agent.sh` 一键部署 |
| 主机群组 | `hostgroups/hostgroups_50.xml`（50 个集合） |

更高版本 Zabbix（4/5/6/7）前端导入时一般可自动转换。

---

## 20 套精简模板一览

目录：[`templates/`](templates/)（索引见 [`templates/INDEX.md`](templates/INDEX.md)）

| # | 文件 | 模板名 | 说明 |
|---|------|--------|------|
| 1 | `01_Template_OS_Linux.xml` | Template OS Linux Basic | CPU/内存/负载/Agent |
| 2 | `02_Template_App_MySQL.xml` | Template App MySQL Basic | MySQL 核心状态 |
| 3 | `03_Template_App_MongoDB.xml` | Template App MongoDB Basic | MongoDB 连接/ops/内存 |
| 4 | `04_Template_App_Redis.xml` | Template App Redis Basic | Redis 客户端/内存 |
| 5 | `05_Template_App_Nginx.xml` | Template App Nginx Basic | stub_status |
| 6 | `06_Template_App_Apache.xml` | Template App Apache Basic | server-status |
| 7 | `07_Template_App_PostgreSQL.xml` | Template App PostgreSQL Basic | 连接/事务 |
| 8 | `08_Template_App_Memcached.xml` | Template App Memcached Basic | stats |
| 9 | `09_Template_App_RabbitMQ.xml` | Template App RabbitMQ Basic | 管理 API |
| 10 | `10_Template_App_Elasticsearch.xml` | Template App Elasticsearch Basic | cluster health |
| 11 | `11_Template_App_HAProxy.xml` | Template App HAProxy Basic | stats csv |
| 12 | `12_Template_App_PHP_FPM.xml` | Template App PHP-FPM Basic | status 页 |
| 13 | `13_Template_App_Docker.xml` | Template App Docker Basic | 容器数量 |
| 14 | `14_Template_App_Keepalived.xml` | Template App Keepalived Basic | 进程/VIP |
| 15 | `15_Template_App_Zookeeper.xml` | Template App Zookeeper Basic | mntr |
| 16 | `16_Template_App_Kafka.xml` | Template App Kafka Basic | 进程/端口（JMX 可扩展） |
| 17 | `17_Template_App_Tomcat.xml` | Template App Tomcat Basic | 端口/进程（JMX 可扩展） |
| 18 | `18_Template_App_HTTP_Service.xml` | Template App HTTP Service | HTTP 探活 |
| 19 | `19_Template_Net_Common_Ports.xml` | Template Net Common Ports | 常见端口监听 |
| 20 | `20_Template_App_Etcd.xml` | Template App Etcd Basic | etcd metrics |

重新生成这 20 套：

```bash
python3 tools/generate_templates.py
```

---

## 经典完整模板（根目录）

监控项更全，适合已在用旧版的环境：

| 文件 | 说明 |
|------|------|
| `Templates_Mysql.xml` | MySQL SHOW STATUS 完整版 |
| `Templates_Mongodb.xml` | MongoDB 完整版（注意默认端口常为 28018） |
| `Templates_mongod_port_is_20717.xml` | MongoDB 完整版（端口按 27017） |
| `zabbix_redis.xml` | Redis 6379 完整版 |
| `Nginx-template.xml` | Nginx 完整版 |

新环境优先用 `templates/` 精简套件；需要更细指标再叠加经典完整版。

---

## 快速开始

### 1. 导入 50 个主机群组（可选）

```text
hostgroups/hostgroups_50.xml
```

或：

```bash
python3 tools/create_hostgroups.py --list
export ZABBIX_URL=http://127.0.0.1/zabbix/api_jsonrpc.php
export ZABBIX_USER=Admin
export ZABBIX_PASSWORD=zabbix
python3 tools/create_hostgroups.py --api
```

### 2. 导入模板

前端：`配置` → `模板` → `导入`

- 精简 20 套：导入 `templates/01_*.xml` … `templates/20_*.xml`
- 或按需只导对应组件

### 3. 部署 Agent 脚本

```bash
sudo ./install_agent.sh
```

会安装：

- `scripts/`（含 `extras/app_metrics.sh`）
- `conf/userparameter_*.conf`（含 `userparameter_extras.conf`）

确认：

```ini
Include=/etc/zabbix/zabbix_agentd.d/*.conf
```

### 4. 主机链接模板 + 改宏

常见宏：

| 宏 | 用于 | 默认示例 |
|----|------|----------|
| `{$NGINX_STATUS_URL}` | Nginx | `http://127.0.0.1/nginx_status` |
| `{$APACHE_STATUS_URL}` | Apache | `http://127.0.0.1/server-status?auto` |
| `{$PHP_FPM_STATUS_URL}` | PHP-FPM | `http://127.0.0.1/php-fpm-status` |
| `{$HAPROXY_STATS_URL}` | HAProxy | `http://127.0.0.1:8080/stats;csv` |
| `{$ES_URL}` | Elasticsearch | `http://127.0.0.1:9200` |
| `{$RABBIT_API}` | RabbitMQ | `http://127.0.0.1:15672` |
| `{$ZK_HOST}` | Zookeeper | `127.0.0.1:2181` |
| `{$HTTP_URL}` | HTTP 探活 | `http://127.0.0.1/` |
| `{$ETCD_URL}` | Etcd | `http://127.0.0.1:2379` |
| `{$KEEPALIVED_VIP}` | Keepalived | `10.0.0.100` |

---

## 组件配置要点

### Linux / 端口 / HTTP

- Linux、Common Ports 主要用 Agent 内置 key，无需额外脚本。
- HTTP：`web.http.*` 由 `app_metrics.sh http` 实现。

### MySQL / Redis / MongoDB / Nginx

沿用原脚本：

```bash
sudo -u zabbix /etc/zabbix/scripts/mysql/mysql_status.sh Ping
/etc/zabbix/scripts/redis/redis_stats.sh 6379 connected_clients
python3 /etc/zabbix/scripts/mongodb/mongodb_status.py version
/etc/zabbix/scripts/nginx/nginx_status.sh active_connections http://127.0.0.1/nginx_status
```

MySQL 建议 `/etc/zabbix/.my.cnf`；MongoDB 需 `pymongo`；Redis 可用 `REDIS_PASSWORD`。

### 扩展组件（Apache / PG / ES / …）

统一入口：

```bash
/etc/zabbix/scripts/extras/app_metrics.sh apache BusyWorkers 'http://127.0.0.1/server-status?auto'
/etc/zabbix/scripts/extras/app_metrics.sh pgsql connections
/etc/zabbix/scripts/extras/app_metrics.sh elasticsearch status http://127.0.0.1:9200
/etc/zabbix/scripts/extras/app_metrics.sh docker running
```

说明：

- **Kafka / Tomcat** 高级指标脚本为占位（默认 0），进程/端口触发器已可用；生产可接 JMX/Exporter 替换。
- **RabbitMQ** 默认 `guest:guest`，可用 `RABBIT_USER` / `RABBIT_PASS`。
- **PostgreSQL** 依赖本机 `psql` 与 `PGUSER`/`PGHOST` 等环境变量。

---

## zabbix_get 验收示例

```bash
zabbix_get -s <ip> -k 'agent.ping'
zabbix_get -s <ip> -k 'mysql.status[Ping]'
zabbix_get -s <ip> -k 'redis_stats[6379,connected_clients]'
zabbix_get -s <ip> -k 'MongoDB.Status[connections,current]'
zabbix_get -s <ip> -k 'nginx[active_connections,http://127.0.0.1/nginx_status]'
zabbix_get -s <ip> -k 'pgsql.ping'
zabbix_get -s <ip> -k 'docker[running]'
zabbix_get -s <ip> -k 'web.http.alive[http://127.0.0.1/]'
```

---

## 目录结构

```text
Zabbix_Temple/
├── README.md
├── install_agent.sh
├── templates/                 # 20 套精简模板（推荐）
│   ├── 01_...xml … 20_...xml
│   └── INDEX.md
├── Templates_Mysql.xml        # 经典完整版
├── Templates_Mongodb.xml
├── Templates_mongod_port_is_20717.xml
├── zabbix_redis.xml
├── Nginx-template.xml
├── conf/
│   ├── userparameter_*.conf
│   └── userparameter_extras.conf
├── scripts/
│   ├── mysql/ redis/ nginx/ mongodb/
│   └── extras/app_metrics.sh
├── hostgroups/hostgroups_50.xml
└── tools/
    ├── create_hostgroups.py
    └── generate_templates.py
```

---

## 验证清单

- [ ] 已导入需要的精简模板（最多 20 套）或经典完整版
- [ ] 已导入 50 主机群组（可选）
- [ ] `sudo ./install_agent.sh` 成功，Agent 已重启
- [ ] 相关宏已按环境修改
- [ ] `zabbix_get` 关键 key 有值
- [ ] 前端「最新数据」正常，误报端口已纠正

---

## 常见问题

| 现象 | 排查 |
|------|------|
| `ZBX_NOTSUPPORTED` | UserParameter 未加载；脚本无执行权限；缺依赖（`curl`/`nc`/`psql`/`pymongo`） |
| MongoDB 端口告警 | 模板端口与真实端口不一致 |
| Nginx/Apache/PHP-FPM 空值 | status 页未开，或宏 URL 不对 |
| Kafka/Tomcat 指标一直为 0 | 当前为占位实现，需自行接 JMX/Exporter |
| RabbitMQ 取数失败 | 管理插件未开，或账号密码不对 |

---

## 备注

- 生产环境请使用最小权限账号访问 DB / MQ / ES。
- `markdown.md` 仅为仓库徽章页，与监控无关。
- 欢迎 Issue / PR 补充更多模板或完善 Kafka/Tomcat 采集。

# Zabbix_Temple

Zabbix 常用监控模板 + Agent 脚本仓库：覆盖 **MongoDB / MySQL / Redis / Nginx**，并附带可导入的 **50 个主机群组（集合）**。

| 项目 | 说明 |
|------|------|
| 模板格式 | 多为 Zabbix **2.0 / 3.0** 导出 XML（见各文件 `<version>`） |
| 更高版本 | Zabbix 4/5/6/7 前端导入时一般可自动转换 |
| 采集方式 | Zabbix Agent + `UserParameter`（脚本在 `scripts/`） |

---

## 仓库一览

| 文件 / 目录 | 作用 |
|-------------|------|
| `Templates_Mongodb.xml` | MongoDB 模板（端口检测常见默认 **28018**，务必改成实际端口） |
| `Templates_mongod_port_is_20717.xml` | MongoDB 模板（端口项按 **27017**） |
| `Templates_Mysql.xml` | MySQL `SHOW STATUS` 模板 |
| `zabbix_redis.xml` | Redis（默认端口 **6379**）模板 |
| `Nginx-template.xml` | Nginx `stub_status` 模板 |
| `scripts/` | Agent 端采集脚本 |
| `conf/` | `UserParameter` 配置样例 |
| `hostgroups/hostgroups_50.xml` | **50 个主机群组**，前端可直接导入 |
| `tools/create_hostgroups.py` | 生成 XML / 通过 API 创建 50 个群组 |
| `install_agent.sh` | 一键把脚本和 conf 装到被监控机 |

---

## 快速开始（推荐顺序）

### 1. 导入 50 个主机群组（可选但建议）

Zabbix 前端：`配置` → `导入`，选择：

```text
hostgroups/hostgroups_50.xml
```

或用脚本：

```bash
python3 tools/create_hostgroups.py --list
python3 tools/create_hostgroups.py --xml > hostgroups/hostgroups_50.xml

export ZABBIX_URL=http://127.0.0.1/zabbix/api_jsonrpc.php
export ZABBIX_USER=Admin
export ZABBIX_PASSWORD=zabbix
python3 tools/create_hostgroups.py --api
```

### 2. 导入监控模板

`配置` → `模板` → `导入`：

| 组件 | 导入文件 |
|------|----------|
| MongoDB | `Templates_Mongodb.xml` 或 `Templates_mongod_port_is_20717.xml` |
| MySQL | `Templates_Mysql.xml` |
| Redis | `zabbix_redis.xml` |
| Nginx | `Nginx-template.xml` |

### 3. 在被监控机部署 Agent 脚本

仓库根目录执行（需 root）：

```bash
sudo ./install_agent.sh
```

等价手工步骤：

```bash
sudo mkdir -p /etc/zabbix/scripts /etc/zabbix/zabbix_agentd.d
sudo cp -r scripts/* /etc/zabbix/scripts/
sudo cp conf/userparameter_*.conf /etc/zabbix/zabbix_agentd.d/
sudo chmod +x /etc/zabbix/scripts/*/*.sh /etc/zabbix/scripts/mongodb/*.py
sudo systemctl restart zabbix-agent   # 或 zabbix-agent2
```

确认 Agent 主配置包含：

```ini
Include=/etc/zabbix/zabbix_agentd.d/*.conf
```

### 4. 主机链接模板

`配置` → `主机` → 选主机 → `模板` → 链接对应模板，并把主机放进合适的群组。

---

## 各组件配置要点

### MongoDB

1. 链接模板后，**检查端口监控项**：`Templates_Mongodb.xml` 常为 `28018`，不改会误报；优先用 `Templates_mongod_port_is_20717.xml`，或批量改成真实端口。
2. 若监控项类型不是 Agent，在模板里批量改为 **Zabbix 客户端**。
3. 依赖：`python3`、`pymongo`。可选环境变量：`MONGO_URI` / `MONGO_HOST` / `MONGO_PORT`。

```bash
pip3 install pymongo
python3 scripts/mongodb/mongodb_status.py version
python3 scripts/mongodb/mongodb_status.py connections current
```

最新数据里端口状态 `1` = 监听正常。

### MySQL

1. 创建只读账号，建议用配置文件（避免密码出现在进程列表）：

```ini
# /etc/zabbix/.my.cnf
[client]
user=zabbix
password=your_password
host=127.0.0.1
```

```bash
sudo chown zabbix:zabbix /etc/zabbix/.my.cnf
sudo chmod 600 /etc/zabbix/.my.cnf
```

2. 本地测试：

```bash
sudo -u zabbix /etc/zabbix/scripts/mysql/mysql_status.sh Ping
sudo -u zabbix /etc/zabbix/scripts/mysql/mysql_status.sh Threads_connected
```

### Redis

1. 模板键格式：`redis_stats[6379,<metric>]`。换端口时同步改模板键或脚本调用端口。
2. 有密码时设置环境变量 `REDIS_PASSWORD`（可写在 systemd `Environment=`）。
3. 模板中个别键为 `used_memory:`，脚本已兼容去掉末尾冒号。

```bash
/etc/zabbix/scripts/redis/redis_stats.sh 6379 connected_clients
/etc/zabbix/scripts/redis/redis_stats.sh 6379 used_memory
```

### Nginx

1. 开启 stub_status：

```nginx
location /nginx_status {
    stub_status on;
    allow 127.0.0.1;
    deny all;
}
```

2. 在主机或模板上设置宏 `{$NGINX_STATUS_URL}`，例如 `http://127.0.0.1/nginx_status`。

```bash
/etc/zabbix/scripts/nginx/nginx_status.sh active_connections http://127.0.0.1/nginx_status
```

---

## 用 zabbix_get 验收

在 Zabbix Server / Proxy 上：

```bash
zabbix_get -s <agent_ip> -k 'mysql.status[Ping]'
zabbix_get -s <agent_ip> -k 'redis_stats[6379,connected_clients]'
zabbix_get -s <agent_ip> -k 'nginx[active_connections,http://127.0.0.1/nginx_status]'
zabbix_get -s <agent_ip> -k 'MongoDB.Status[version]'
zabbix_get -s <agent_ip> -k 'MongoDB.Status[connections,current]'
```

能返回正常值后，再到前端看「最新数据」。

---

## 50 个主机群组说明

`hostgroups/hostgroups_50.xml` / `tools/create_hostgroups.py` 内置 50 个集合，大致分类：

- 操作系统 / 基础设施（Linux、Windows、VM、容器节点等）
- 中间件与数据库（MySQL、MongoDB、Redis、Nginx、Kafka 等）
- 环境分层（Production / Staging / Testing / Development / DR）
- 业务角色（Web、API、缓存、消息队列、数据库层等）
- 机房与云（北京/上海/广州、阿里云/AWS/腾讯云、DMZ 等）

完整名单：

```bash
python3 tools/create_hostgroups.py --list
```

---

## 目录结构

```text
Zabbix_Temple/
├── README.md
├── install_agent.sh
├── Templates_Mongodb.xml
├── Templates_mongod_port_is_20717.xml
├── Templates_Mysql.xml
├── zabbix_redis.xml
├── Nginx-template.xml
├── conf/
│   ├── userparameter_mongodb.conf
│   ├── userparameter_mysql.conf
│   ├── userparameter_nginx.conf
│   └── userparameter_redis.conf
├── scripts/
│   ├── mongodb/mongodb_status.py
│   ├── mysql/mysql_status.sh
│   ├── nginx/nginx_status.sh
│   └── redis/redis_stats.sh
├── hostgroups/
│   └── hostgroups_50.xml
└── tools/
    └── create_hostgroups.py
```

---

## 验证清单

- [ ] `hostgroups_50.xml` 已导入（或 API 创建成功）
- [ ] 所需模板已导入，主机已链接
- [ ] 已执行 `install_agent.sh`（或等价拷贝），Agent 已重启
- [ ] `Include=.../zabbix_agentd.d/*.conf` 生效
- [ ] `zabbix_get` 各 key 有返回值
- [ ] MongoDB 端口 / Nginx 宏 / Redis 端口已按环境改对
- [ ] 前端「最新数据」正常刷新，无长期误报

---

## 常见问题

| 现象 | 排查 |
|------|------|
| `ZBX_NOTSUPPORTED` | Agent 未加载 UserParameter；脚本路径不对；依赖未装（如 `pymongo`、`redis-cli`、`mysql`、`curl`） |
| MongoDB 端口一直告警 | 模板端口与真实监听端口不一致 |
| Nginx 全是空值 | `stub_status` 未开，或 `{$NGINX_STATUS_URL}` 不对 |
| MySQL 取不到值 | `/etc/zabbix/.my.cnf` 权限/属主不对，或账号无权限 |
| Redis 取不到值 | 端口/密码不对；确认 `redis-cli -p <port> INFO` 本机可用 |

---

## 备注

- 生产环境请为 MySQL / MongoDB / Redis 使用**最小权限**只读账号，勿用 root。
- `markdown.md` 为仓库动态徽章页，与监控逻辑无关。
- 问题反馈或补充模板可直接提 Issue / PR。

# Templates catalog (20)

| # | File | Template | Description |
|---|------|----------|-------------|
| 1 | `01_Template_OS_Linux.xml` | Template OS Linux Basic | Linux 基础 Agent 监控：CPU/内存/负载/交换/Agent 存活 |
| 2 | `02_Template_App_MySQL.xml` | Template App MySQL Basic | MySQL 精简监控（配合 scripts/mysql + mysql.status[*]） |
| 3 | `03_Template_App_MongoDB.xml` | Template App MongoDB Basic | MongoDB 精简监控（配合 scripts/mongodb + MongoDB.Status[*]），默认端口 27017 |
| 4 | `04_Template_App_Redis.xml` | Template App Redis Basic | Redis 精简监控（配合 scripts/redis + redis_stats[6379,*]） |
| 5 | `05_Template_App_Nginx.xml` | Template App Nginx Basic | Nginx stub_status 精简监控，宏 {$NGINX_STATUS_URL} |
| 6 | `06_Template_App_Apache.xml` | Template App Apache Basic | Apache server-status 精简监控，宏 {$APACHE_STATUS_URL} |
| 7 | `07_Template_App_PostgreSQL.xml` | Template App PostgreSQL Basic | PostgreSQL 精简监控（pgsql.* UserParameter） |
| 8 | `08_Template_App_Memcached.xml` | Template App Memcached Basic | Memcached stats 精简监控 |
| 9 | `09_Template_App_RabbitMQ.xml` | Template App RabbitMQ Basic | RabbitMQ 管理 API 精简监控，宏 {$RABBIT_API} |
| 10 | `10_Template_App_Elasticsearch.xml` | Template App Elasticsearch Basic | Elasticsearch _cluster/health 精简监控 |
| 11 | `11_Template_App_HAProxy.xml` | Template App HAProxy Basic | HAProxy stats 精简监控，宏 {$HAPROXY_STATS_URL} |
| 12 | `12_Template_App_PHP_FPM.xml` | Template App PHP-FPM Basic | PHP-FPM status 精简监控，宏 {$PHP_FPM_STATUS_URL} |
| 13 | `13_Template_App_Docker.xml` | Template App Docker Basic | Docker 守护进程与容器数量精简监控 |
| 14 | `14_Template_App_Keepalived.xml` | Template App Keepalived Basic | Keepalived 进程与 VIP 相关精简监控 |
| 15 | `15_Template_App_Zookeeper.xml` | Template App Zookeeper Basic | Zookeeper mntr 精简监控，宏 {$ZK_HOST} |
| 16 | `16_Template_App_Kafka.xml` | Template App Kafka Basic | Kafka 进程与端口精简监控（可扩展 JMX） |
| 17 | `17_Template_App_Tomcat.xml` | Template App Tomcat Basic | Tomcat/JVM 进程与 HTTP 端口精简监控 |
| 18 | `18_Template_App_HTTP_Service.xml` | Template App HTTP Service | HTTP/HTTPS 站点可用性精简监控，宏 {$HTTP_URL} |
| 19 | `19_Template_Net_Common_Ports.xml` | Template Net Common Ports | 常见服务端口监听检查合集 |
| 20 | `20_Template_App_Etcd.xml` | Template App Etcd Basic | Etcd metrics 精简监控，宏 {$ETCD_URL} |

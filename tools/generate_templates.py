#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成约 20 套可导入的 Zabbix 3.0 模板 XML。"""

from __future__ import print_function

import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(ROOT, "templates")

COLORS = ["C80000", "00C800", "0000C8", "C8C800", "00C8C8", "C800C8", "960000", "009600"]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def item_xml(name, key, app, value_type=3, units="", delay=60, history=7, delta=0):
    return """                <item>
                    <name>{name}</name>
                    <type>0</type>
                    <snmp_community/>
                    <multiplier>0</multiplier>
                    <snmp_oid/>
                    <key>{key}</key>
                    <delay>{delay}</delay>
                    <history>{history}</history>
                    <trends>365</trends>
                    <status>0</status>
                    <value_type>{value_type}</value_type>
                    <allowed_hosts/>
                    <units>{units}</units>
                    <delta>{delta}</delta>
                    <snmpv3_contextname/>
                    <snmpv3_securityname/>
                    <snmpv3_securitylevel>0</snmpv3_securitylevel>
                    <snmpv3_authprotocol>0</snmpv3_authprotocol>
                    <snmpv3_authpassphrase/>
                    <snmpv3_privprotocol>0</snmpv3_privprotocol>
                    <snmpv3_privpassphrase/>
                    <formula>1</formula>
                    <delay_flex/>
                    <params/>
                    <ipmi_sensor/>
                    <data_type>0</data_type>
                    <authtype>0</authtype>
                    <username/>
                    <password/>
                    <publickey/>
                    <privatekey/>
                    <port/>
                    <description/>
                    <inventory_link>0</inventory_link>
                    <applications>
                        <application>
                            <name>{app}</name>
                        </application>
                    </applications>
                    <valuemap/>
                </item>""".format(
        name=escape(name),
        key=escape(key),
        app=escape(app),
        value_type=value_type,
        units=escape(units),
        delay=delay,
        history=history,
        delta=delta,
    )


def trigger_xml(template, key, name, priority=4, last=0):
    # last=0 means .last()=0 ; otherwise use count style for listen
    if last == "nodata":
        expr = "{{{tpl}:{key}.nodata(5m)}}=1".format(tpl=template, key=key)
    elif last == "listen":
        expr = "{{{tpl}:{key}.last()}}=0".format(tpl=template, key=key)
    else:
        expr = "{{{tpl}:{key}.last()}}={val}".format(tpl=template, key=key, val=last)
    return """        <trigger>
            <expression>{expr}</expression>
            <name>{name}</name>
            <url/>
            <status>0</status>
            <priority>{priority}</priority>
            <description/>
            <type>0</type>
            <dependencies/>
        </trigger>""".format(
        expr=escape(expr),
        name=escape(name),
        priority=priority,
    )


def graph_xml(template, title, keys):
    items = []
    for i, key in enumerate(keys):
        items.append(
            """                <graph_item>
                    <sortorder>{i}</sortorder>
                    <drawtype>0</drawtype>
                    <color>{color}</color>
                    <yaxisside>0</yaxisside>
                    <calc_fnc>2</calc_fnc>
                    <type>0</type>
                    <item>
                        <host>{host}</host>
                        <key>{key}</key>
                    </item>
                </graph_item>""".format(
                i=i,
                color=COLORS[i % len(COLORS)],
                host=escape(template),
                key=escape(key),
            )
        )
    return """        <graph>
            <name>{title}</name>
            <width>900</width>
            <height>200</height>
            <yaxismin>0.0000</yaxismin>
            <yaxismax>100.0000</yaxismax>
            <show_work_period>1</show_work_period>
            <show_triggers>1</show_triggers>
            <type>0</type>
            <show_legend>1</show_legend>
            <show_3d>0</show_3d>
            <percent_left>0.0000</percent_left>
            <percent_right>0.0000</percent_right>
            <ymin_type_1>0</ymin_type_1>
            <ymax_type_1>0</ymax_type_1>
            <ymin_item_1>0</ymin_item_1>
            <ymax_item_1>0</ymax_item_1>
            <graph_items>
{items}
            </graph_items>
        </graph>""".format(
        title=escape(title),
        items="\n".join(items),
    )


def macro_xml(macros):
    if not macros:
        return "            <macros/>"
    lines = ["            <macros>"]
    for m, v in macros:
        lines.append("                <macro>")
        lines.append("                    <macro>{}</macro>".format(escape(m)))
        lines.append("                    <value>{}</value>".format(escape(v)))
        lines.append("                </macro>")
    lines.append("            </macros>")
    return "\n".join(lines)


def build_template(spec):
    """
    spec keys:
      file, template, name, app, description, items[(name,key,vt,units,delta)],
      triggers[(key,name,priority,mode)], graphs[(title,[keys])], macros[(k,v)]
    """
    template = spec["template"]
    app = spec["app"]
    apps = "\n".join(
        [
            "                <application>",
            "                    <name>{}</name>".format(escape(app)),
            "                </application>",
        ]
    )
    items = "\n".join(
        item_xml(
            n,
            k,
            app,
            value_type=vt,
            units=units,
            delta=delta,
        )
        for (n, k, vt, units, delta) in spec["items"]
    )
    triggers = "\n".join(
        trigger_xml(template, key, name, priority=pri, last=mode)
        for (key, name, pri, mode) in spec.get("triggers", [])
    )
    graphs = "\n".join(
        graph_xml(template, title, keys) for (title, keys) in spec.get("graphs", [])
    )
    macros = macro_xml(spec.get("macros", []))
    desc = escape(spec.get("description", ""))

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<zabbix_export>
    <version>3.0</version>
    <date>{date}</date>
    <groups>
        <group>
            <name>Templates</name>
        </group>
    </groups>
    <templates>
        <template>
            <template>{template}</template>
            <name>{name}</name>
            <description>{desc}</description>
            <groups>
                <group>
                    <name>Templates</name>
                </group>
            </groups>
            <applications>
{apps}
            </applications>
            <items>
{items}
            </items>
            <discovery_rules/>
{macros}
            <templates/>
            <screens/>
        </template>
    </templates>
    <triggers>
{triggers}
    </triggers>
    <graphs>
{graphs}
    </graphs>
</zabbix_export>
""".format(
        date=now_iso(),
        template=escape(template),
        name=escape(spec["name"]),
        desc=desc,
        apps=apps,
        items=items,
        macros=macros,
        triggers=triggers or "",
        graphs=graphs or "",
    )
    return xml


def u(name, key, units="", delta=0, vt=3):
    return (name, key, vt, units, delta)


def f(name, key, units="", delta=0):
    return (name, key, 0, units, delta)


def t(name, key):
    return (name, key, 4, "", 0)


def c(name, key):
    return (name, key, 1, "", 0)


TEMPLATES = [
    {
        "file": "01_Template_OS_Linux.xml",
        "template": "Template OS Linux Basic",
        "name": "Template OS Linux Basic",
        "app": "OS Linux",
        "description": "Linux 基础 Agent 监控：CPU/内存/负载/交换/Agent 存活",
        "items": [
            f("CPU idle time", "system.cpu.util[,idle]", "%"),
            f("CPU user time", "system.cpu.util[,user]", "%"),
            f("CPU system time", "system.cpu.util[,system]", "%"),
            f("CPU load (1m avg per core)", "system.cpu.load[percpu,avg1]"),
            f("CPU load (5m avg per core)", "system.cpu.load[percpu,avg5]"),
            u("Total memory", "vm.memory.size[total]", "B"),
            u("Available memory", "vm.memory.size[available]", "B"),
            f("Memory utilization", "vm.memory.size[pavailable]", "%"),
            u("Total swap", "system.swap.size[,total]", "B"),
            f("Free swap percent", "system.swap.size[,pfree]", "%"),
            u("Number of processes", "proc.num[]"),
            u("Number of running processes", "proc.num[,,run]"),
            u("System uptime", "system.uptime", "uptime"),
            c("System hostname", "system.hostname"),
            c("System uname", "system.uname"),
            u("Agent ping", "agent.ping"),
            c("Agent version", "agent.version"),
        ],
        "triggers": [
            ("agent.ping", "Zabbix agent on {HOST.NAME} is unreachable", 5, "nodata"),
        ],
        "graphs": [
            ("CPU utilization", ["system.cpu.util[,idle]", "system.cpu.util[,user]", "system.cpu.util[,system]"]),
            ("CPU load", ["system.cpu.load[percpu,avg1]", "system.cpu.load[percpu,avg5]"]),
            ("Memory", ["vm.memory.size[available]", "vm.memory.size[total]"]),
        ],
    },
    {
        "file": "02_Template_App_MySQL.xml",
        "template": "Template App MySQL Basic",
        "name": "Template App MySQL Basic",
        "app": "MySQL",
        "description": "MySQL 精简监控（配合 scripts/mysql + mysql.status[*]）",
        "items": [
            u("MySQL ping", "mysql.status[Ping]"),
            u("MySQL uptime", "mysql.status[Uptime]", "uptime"),
            u("Threads connected", "mysql.status[Threads_connected]"),
            u("Threads running", "mysql.status[Threads_running]"),
            u("Questions", "mysql.status[Questions]", "", 1),
            u("Slow queries", "mysql.status[Slow_queries]", "", 1),
            u("Com select", "mysql.status[Com_select]", "", 1),
            u("Com insert", "mysql.status[Com_insert]", "", 1),
            u("Com update", "mysql.status[Com_update]", "", 1),
            u("Com delete", "mysql.status[Com_delete]", "", 1),
            u("Bytes received", "mysql.status[Bytes_received]", "B", 1),
            u("Bytes sent", "mysql.status[Bytes_sent]", "B", 1),
            u("MySQL port listen 3306", "net.tcp.listen[3306]"),
            t("MySQL version", "mysql.status[Version]"),
        ],
        "triggers": [
            ("mysql.status[Ping]", "MySQL is down on {HOST.NAME}", 5, 0),
            ("net.tcp.listen[3306]", "MySQL port 3306 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("MySQL threads", ["mysql.status[Threads_connected]", "mysql.status[Threads_running]"]),
            ("MySQL QPS ops", ["mysql.status[Com_select]", "mysql.status[Com_insert]", "mysql.status[Com_update]", "mysql.status[Com_delete]"]),
        ],
    },
    {
        "file": "03_Template_App_MongoDB.xml",
        "template": "Template App MongoDB Basic",
        "name": "Template App MongoDB Basic",
        "app": "MongoDB",
        "description": "MongoDB 精简监控（配合 scripts/mongodb + MongoDB.Status[*]），默认端口 27017",
        "items": [
            u("MongoDB port 27017", "net.tcp.listen[27017]"),
            t("MongoDB version", "MongoDB.Status[version]"),
            t("MongoDB process", "MongoDB.Status[process]"),
            u("MongoDB uptime", "MongoDB.Status[uptime]", "uptime"),
            u("Connections current", "MongoDB.Status[connections,current]"),
            u("Connections available", "MongoDB.Status[connections,available]"),
            u("Network bytesIn", "MongoDB.Status[network,bytesIn]", "B", 1),
            u("Network bytesOut", "MongoDB.Status[network,bytesOut]", "B", 1),
            u("Opcounters insert", "MongoDB.Status[opcounters,insert]", "", 1),
            u("Opcounters query", "MongoDB.Status[opcounters,query]", "", 1),
            u("Opcounters update", "MongoDB.Status[opcounters,update]", "", 1),
            u("Opcounters delete", "MongoDB.Status[opcounters,delete]", "", 1),
            u("Mem resident", "MongoDB.Status[mem,resident]", "B"),
            u("Mem virtual", "MongoDB.Status[mem,virtual]", "B"),
        ],
        "triggers": [
            ("net.tcp.listen[27017]", "MongoDB port 27017 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("MongoDB connections", ["MongoDB.Status[connections,current]", "MongoDB.Status[connections,available]"]),
            ("MongoDB opcounters", ["MongoDB.Status[opcounters,insert]", "MongoDB.Status[opcounters,query]", "MongoDB.Status[opcounters,update]", "MongoDB.Status[opcounters,delete]"]),
        ],
    },
    {
        "file": "04_Template_App_Redis.xml",
        "template": "Template App Redis Basic",
        "name": "Template App Redis Basic",
        "app": "Redis",
        "description": "Redis 精简监控（配合 scripts/redis + redis_stats[6379,*]）",
        "items": [
            u("Redis port 6379", "net.tcp.listen[6379]"),
            u("Connected clients", "redis_stats[6379,connected_clients]"),
            u("Blocked clients", "redis_stats[6379,blocked_clients]"),
            u("Used memory", "redis_stats[6379,used_memory]", "B"),
            u("Used memory RSS", "redis_stats[6379,used_memory_rss]", "B"),
            u("Total commands processed", "redis_stats[6379,total_commands_processed]", "", 1),
            u("Total connections received", "redis_stats[6379,total_connections_received]", "", 1),
            u("Expired keys", "redis_stats[6379,expired_keys]", "", 1),
            u("Evicted keys", "redis_stats[6379,evicted_keys]", "", 1),
            u("Uptime seconds", "redis_stats[6379,uptime_in_seconds]", "uptime"),
            c("Redis role", "redis_stats[6379,role]"),
        ],
        "triggers": [
            ("net.tcp.listen[6379]", "Redis port 6379 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("Redis clients", ["redis_stats[6379,connected_clients]", "redis_stats[6379,blocked_clients]"]),
            ("Redis memory", ["redis_stats[6379,used_memory]", "redis_stats[6379,used_memory_rss]"]),
        ],
    },
    {
        "file": "05_Template_App_Nginx.xml",
        "template": "Template App Nginx Basic",
        "name": "Template App Nginx Basic",
        "app": "Nginx",
        "description": "Nginx stub_status 精简监控，宏 {$NGINX_STATUS_URL}",
        "macros": [("{NGINX_STATUS_URL}", "http://127.0.0.1/nginx_status")],
        "items": [
            u("Nginx active connections", "nginx[active_connections,{$NGINX_STATUS_URL}]"),
            u("Nginx reading", "nginx[reading,{$NGINX_STATUS_URL}]"),
            u("Nginx writing", "nginx[writing,{$NGINX_STATUS_URL}]"),
            u("Nginx waiting", "nginx[waiting,{$NGINX_STATUS_URL}]"),
            u("Nginx accepted", "nginx[accepted_connections,{$NGINX_STATUS_URL}]", "", 1),
            u("Nginx handled", "nginx[handled_connections,{$NGINX_STATUS_URL}]", "", 1),
            u("Nginx requests", "nginx[handled_requests,{$NGINX_STATUS_URL}]", "", 1),
            u("Nginx process", "proc.num[nginx]"),
        ],
        "triggers": [
            ("proc.num[nginx]", "Nginx is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("Nginx connections", ["nginx[active_connections,{$NGINX_STATUS_URL}]", "nginx[reading,{$NGINX_STATUS_URL}]", "nginx[writing,{$NGINX_STATUS_URL}]", "nginx[waiting,{$NGINX_STATUS_URL}]"]),
        ],
    },
    {
        "file": "06_Template_App_Apache.xml",
        "template": "Template App Apache Basic",
        "name": "Template App Apache Basic",
        "app": "Apache",
        "description": "Apache server-status 精简监控，宏 {$APACHE_STATUS_URL}",
        "macros": [("{APACHE_STATUS_URL}", "http://127.0.0.1/server-status?auto")],
        "items": [
            u("Apache Total Accesses", "apache[TotalAccesses,{$APACHE_STATUS_URL}]", "", 1),
            u("Apache Total kBytes", "apache[TotalkBytes,{$APACHE_STATUS_URL}]", "B", 1),
            f("Apache CPULoad", "apache[CPULoad,{$APACHE_STATUS_URL}]"),
            u("Apache Uptime", "apache[Uptime,{$APACHE_STATUS_URL}]", "uptime"),
            f("Apache ReqBusyWorkers", "apache[BusyWorkers,{$APACHE_STATUS_URL}]"),
            f("Apache IdleWorkers", "apache[IdleWorkers,{$APACHE_STATUS_URL}]"),
            u("Apache process", "proc.num[httpd]"),
            u("Apache port 80", "net.tcp.listen[80]"),
        ],
        "triggers": [
            ("proc.num[httpd]", "Apache httpd is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("Apache workers", ["apache[BusyWorkers,{$APACHE_STATUS_URL}]", "apache[IdleWorkers,{$APACHE_STATUS_URL}]"]),
        ],
    },
    {
        "file": "07_Template_App_PostgreSQL.xml",
        "template": "Template App PostgreSQL Basic",
        "name": "Template App PostgreSQL Basic",
        "app": "PostgreSQL",
        "description": "PostgreSQL 精简监控（pgsql.* UserParameter）",
        "items": [
            u("PostgreSQL ping", "pgsql.ping"),
            u("PostgreSQL connections", "pgsql.connections"),
            u("PostgreSQL active queries", "pgsql.active"),
            u("PostgreSQL idle queries", "pgsql.idle"),
            u("PostgreSQL tx commits", "pgsql.commits", "", 1),
            u("PostgreSQL tx rollbacks", "pgsql.rollbacks", "", 1),
            u("PostgreSQL deadlocks", "pgsql.deadlocks", "", 1),
            u("PostgreSQL port 5432", "net.tcp.listen[5432]"),
            t("PostgreSQL version", "pgsql.version"),
        ],
        "triggers": [
            ("pgsql.ping", "PostgreSQL is down on {HOST.NAME}", 5, 0),
            ("net.tcp.listen[5432]", "PostgreSQL port 5432 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("PostgreSQL connections", ["pgsql.connections", "pgsql.active", "pgsql.idle"]),
        ],
    },
    {
        "file": "08_Template_App_Memcached.xml",
        "template": "Template App Memcached Basic",
        "name": "Template App Memcached Basic",
        "app": "Memcached",
        "description": "Memcached stats 精简监控",
        "items": [
            u("Memcached port 11211", "net.tcp.listen[11211]"),
            u("Memcached curr items", "memcached[curr_items]"),
            u("Memcached total items", "memcached[total_items]", "", 1),
            u("Memcached bytes", "memcached[bytes]", "B"),
            u("Memcached limit maxbytes", "memcached[limit_maxbytes]", "B"),
            u("Memcached curr connections", "memcached[curr_connections]"),
            u("Memcached get hits", "memcached[get_hits]", "", 1),
            u("Memcached get misses", "memcached[get_misses]", "", 1),
            u("Memcached evictions", "memcached[evictions]", "", 1),
            u("Memcached process", "proc.num[memcached]"),
        ],
        "triggers": [
            ("net.tcp.listen[11211]", "Memcached port 11211 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("Memcached items", ["memcached[curr_items]"]),
            ("Memcached hits/misses", ["memcached[get_hits]", "memcached[get_misses]"]),
        ],
    },
    {
        "file": "09_Template_App_RabbitMQ.xml",
        "template": "Template App RabbitMQ Basic",
        "name": "Template App RabbitMQ Basic",
        "app": "RabbitMQ",
        "description": "RabbitMQ 管理 API 精简监控，宏 {$RABBIT_API}",
        "macros": [("{RABBIT_API}", "http://127.0.0.1:15672")],
        "items": [
            u("RabbitMQ port 5672", "net.tcp.listen[5672]"),
            u("RabbitMQ overview queues", "rabbitmq[queues,{$RABBIT_API}]"),
            u("RabbitMQ overview connections", "rabbitmq[connections,{$RABBIT_API}]"),
            u("RabbitMQ overview consumers", "rabbitmq[consumers,{$RABBIT_API}]"),
            u("RabbitMQ messages ready", "rabbitmq[messages_ready,{$RABBIT_API}]"),
            u("RabbitMQ messages unacked", "rabbitmq[messages_unacknowledged,{$RABBIT_API}]"),
            u("RabbitMQ process", "proc.num[beam.smp]"),
        ],
        "triggers": [
            ("net.tcp.listen[5672]", "RabbitMQ AMQP port 5672 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("RabbitMQ messages", ["rabbitmq[messages_ready,{$RABBIT_API}]", "rabbitmq[messages_unacknowledged,{$RABBIT_API}]"]),
        ],
    },
    {
        "file": "10_Template_App_Elasticsearch.xml",
        "template": "Template App Elasticsearch Basic",
        "name": "Template App Elasticsearch Basic",
        "app": "Elasticsearch",
        "description": "Elasticsearch _cluster/health 精简监控",
        "macros": [("{ES_URL}", "http://127.0.0.1:9200")],
        "items": [
            u("Elasticsearch port 9200", "net.tcp.listen[9200]"),
            c("Cluster status", "elasticsearch[status,{$ES_URL}]"),
            u("Cluster nodes", "elasticsearch[number_of_nodes,{$ES_URL}]"),
            u("Cluster data nodes", "elasticsearch[number_of_data_nodes,{$ES_URL}]"),
            u("Active primary shards", "elasticsearch[active_primary_shards,{$ES_URL}]"),
            u("Active shards", "elasticsearch[active_shards,{$ES_URL}]"),
            u("Unassigned shards", "elasticsearch[unassigned_shards,{$ES_URL}]"),
            u("Relocating shards", "elasticsearch[relocating_shards,{$ES_URL}]"),
            u("Elasticsearch process", "proc.num[java,elasticsearch]"),
        ],
        "triggers": [
            ("net.tcp.listen[9200]", "Elasticsearch port 9200 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("Elasticsearch shards", ["elasticsearch[active_shards,{$ES_URL}]", "elasticsearch[unassigned_shards,{$ES_URL}]"]),
        ],
    },
    {
        "file": "11_Template_App_HAProxy.xml",
        "template": "Template App HAProxy Basic",
        "name": "Template App HAProxy Basic",
        "app": "HAProxy",
        "description": "HAProxy stats 精简监控，宏 {$HAPROXY_STATS_URL}",
        "macros": [("{HAPROXY_STATS_URL}", "http://127.0.0.1:8080/stats;csv")],
        "items": [
            u("HAProxy process", "proc.num[haproxy]"),
            u("HAProxy frontend sessions", "haproxy[frontend_scur,{$HAPROXY_STATS_URL}]"),
            u("HAProxy frontend session rate", "haproxy[frontend_rate,{$HAPROXY_STATS_URL}]"),
            u("HAProxy backend down servers", "haproxy[backend_down,{$HAPROXY_STATS_URL}]"),
            u("HAProxy denied requests", "haproxy[denied_req,{$HAPROXY_STATS_URL}]", "", 1),
            u("HAProxy errors", "haproxy[errors,{$HAPROXY_STATS_URL}]", "", 1),
        ],
        "triggers": [
            ("proc.num[haproxy]", "HAProxy is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("HAProxy sessions", ["haproxy[frontend_scur,{$HAPROXY_STATS_URL}]", "haproxy[frontend_rate,{$HAPROXY_STATS_URL}]"]),
        ],
    },
    {
        "file": "12_Template_App_PHP_FPM.xml",
        "template": "Template App PHP-FPM Basic",
        "name": "Template App PHP-FPM Basic",
        "app": "PHP-FPM",
        "description": "PHP-FPM status 精简监控，宏 {$PHP_FPM_STATUS_URL}",
        "macros": [("{PHP_FPM_STATUS_URL}", "http://127.0.0.1/php-fpm-status")],
        "items": [
            u("PHP-FPM active processes", "phpfpm[active processes,{$PHP_FPM_STATUS_URL}]"),
            u("PHP-FPM idle processes", "phpfpm[idle processes,{$PHP_FPM_STATUS_URL}]"),
            u("PHP-FPM total processes", "phpfpm[total processes,{$PHP_FPM_STATUS_URL}]"),
            u("PHP-FPM listen queue", "phpfpm[listen queue,{$PHP_FPM_STATUS_URL}]"),
            u("PHP-FPM slow requests", "phpfpm[slow requests,{$PHP_FPM_STATUS_URL}]", "", 1),
            u("PHP-FPM process", "proc.num[php-fpm]"),
        ],
        "triggers": [
            ("proc.num[php-fpm]", "PHP-FPM is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("PHP-FPM processes", ["phpfpm[active processes,{$PHP_FPM_STATUS_URL}]", "phpfpm[idle processes,{$PHP_FPM_STATUS_URL}]"]),
        ],
    },
    {
        "file": "13_Template_App_Docker.xml",
        "template": "Template App Docker Basic",
        "name": "Template App Docker Basic",
        "app": "Docker",
        "description": "Docker 守护进程与容器数量精简监控",
        "items": [
            u("Docker process", "proc.num[dockerd]"),
            u("Docker running containers", "docker[running]"),
            u("Docker paused containers", "docker[paused]"),
            u("Docker stopped containers", "docker[stopped]"),
            u("Docker images", "docker[images]"),
            u("Docker port 2375 listen", "net.tcp.listen[2375]"),
        ],
        "triggers": [
            ("proc.num[dockerd]", "Docker daemon is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("Docker containers", ["docker[running]", "docker[paused]", "docker[stopped]"]),
        ],
    },
    {
        "file": "14_Template_App_Keepalived.xml",
        "template": "Template App Keepalived Basic",
        "name": "Template App Keepalived Basic",
        "app": "Keepalived",
        "description": "Keepalived 进程与 VIP 相关精简监控",
        "macros": [("{KEEPALIVED_VIP}", "10.0.0.100")],
        "items": [
            u("Keepalived process", "proc.num[keepalived]"),
            u("Keepalived VIP present", "keepalived[vip,{$KEEPALIVED_VIP}]"),
            u("Keepalived VRRP instances", "keepalived[instances]"),
        ],
        "triggers": [
            ("proc.num[keepalived]", "Keepalived is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("Keepalived VIP", ["keepalived[vip,{$KEEPALIVED_VIP}]"]),
        ],
    },
    {
        "file": "15_Template_App_Zookeeper.xml",
        "template": "Template App Zookeeper Basic",
        "name": "Template App Zookeeper Basic",
        "app": "Zookeeper",
        "description": "Zookeeper mntr 精简监控，宏 {$ZK_HOST}",
        "macros": [("{ZK_HOST}", "127.0.0.1:2181")],
        "items": [
            u("Zookeeper port 2181", "net.tcp.listen[2181]"),
            u("ZK avg latency", "zookeeper[avg_latency,{$ZK_HOST}]"),
            u("ZK max latency", "zookeeper[max_latency,{$ZK_HOST}]"),
            u("ZK packets received", "zookeeper[packets_received,{$ZK_HOST}]", "", 1),
            u("ZK packets sent", "zookeeper[packets_sent,{$ZK_HOST}]", "", 1),
            u("ZK num alive connections", "zookeeper[num_alive_connections,{$ZK_HOST}]"),
            u("ZK outstanding requests", "zookeeper[outstanding_requests,{$ZK_HOST}]"),
            c("ZK server state", "zookeeper[server_state,{$ZK_HOST}]"),
            u("ZK znode count", "zookeeper[znode_count,{$ZK_HOST}]"),
        ],
        "triggers": [
            ("net.tcp.listen[2181]", "Zookeeper port 2181 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("Zookeeper latency", ["zookeeper[avg_latency,{$ZK_HOST}]", "zookeeper[max_latency,{$ZK_HOST}]"]),
        ],
    },
    {
        "file": "16_Template_App_Kafka.xml",
        "template": "Template App Kafka Basic",
        "name": "Template App Kafka Basic",
        "app": "Kafka",
        "description": "Kafka 进程与端口精简监控（可扩展 JMX）",
        "items": [
            u("Kafka process", "proc.num[java,kafka]"),
            u("Kafka port 9092", "net.tcp.listen[9092]"),
            u("Kafka under replicated partitions", "kafka[under_replicated_partitions]"),
            u("Kafka active controller count", "kafka[active_controller_count]"),
            u("Kafka offline partitions", "kafka[offline_partitions_count]"),
        ],
        "triggers": [
            ("net.tcp.listen[9092]", "Kafka port 9092 is down on {HOST.NAME}", 4, "listen"),
            ("proc.num[java,kafka]", "Kafka process is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("Kafka partitions health", ["kafka[under_replicated_partitions]", "kafka[offline_partitions_count]"]),
        ],
    },
    {
        "file": "17_Template_App_Tomcat.xml",
        "template": "Template App Tomcat Basic",
        "name": "Template App Tomcat Basic",
        "app": "Tomcat",
        "description": "Tomcat/JVM 进程与 HTTP 端口精简监控",
        "items": [
            u("Tomcat process", "proc.num[java,org.apache.catalina.startup.Bootstrap]"),
            u("Tomcat HTTP port 8080", "net.tcp.listen[8080]"),
            u("Tomcat AJP port 8009", "net.tcp.listen[8009]"),
            u("JVM heap used", "tomcat[heap_used]", "B"),
            u("JVM heap max", "tomcat[heap_max]", "B"),
            u("Tomcat threads busy", "tomcat[threads_busy]"),
            u("Tomcat threads current", "tomcat[threads_current]"),
            u("Tomcat error count", "tomcat[error_count]", "", 1),
        ],
        "triggers": [
            ("net.tcp.listen[8080]", "Tomcat HTTP port 8080 is down on {HOST.NAME}", 4, "listen"),
        ],
        "graphs": [
            ("Tomcat threads", ["tomcat[threads_busy]", "tomcat[threads_current]"]),
            ("Tomcat heap", ["tomcat[heap_used]", "tomcat[heap_max]"]),
        ],
    },
    {
        "file": "18_Template_App_HTTP_Service.xml",
        "template": "Template App HTTP Service",
        "name": "Template App HTTP Service",
        "app": "HTTP",
        "description": "HTTP/HTTPS 站点可用性精简监控，宏 {$HTTP_URL}",
        "macros": [("{HTTP_URL}", "http://127.0.0.1/")],
        "items": [
            u("HTTP code", "web.http.code[{$HTTP_URL}]"),
            f("HTTP time", "web.http.time[{$HTTP_URL}]", "s"),
            u("HTTP alive", "web.http.alive[{$HTTP_URL}]"),
        ],
        "triggers": [
            ("web.http.alive[{$HTTP_URL}]", "HTTP service is down on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("HTTP response time", ["web.http.time[{$HTTP_URL}]"]),
        ],
    },
    {
        "file": "19_Template_Net_Common_Ports.xml",
        "template": "Template Net Common Ports",
        "name": "Template Net Common Ports",
        "app": "Ports",
        "description": "常见服务端口监听检查合集",
        "items": [
            u("Listen SSH 22", "net.tcp.listen[22]"),
            u("Listen HTTP 80", "net.tcp.listen[80]"),
            u("Listen HTTPS 443", "net.tcp.listen[443]"),
            u("Listen MySQL 3306", "net.tcp.listen[3306]"),
            u("Listen PostgreSQL 5432", "net.tcp.listen[5432]"),
            u("Listen Redis 6379", "net.tcp.listen[6379]"),
            u("Listen MongoDB 27017", "net.tcp.listen[27017]"),
            u("Listen Elasticsearch 9200", "net.tcp.listen[9200]"),
            u("Listen Kafka 9092", "net.tcp.listen[9092]"),
            u("Listen Zookeeper 2181", "net.tcp.listen[2181]"),
        ],
        "triggers": [],
        "graphs": [
            ("Common ports listen map", ["net.tcp.listen[22]", "net.tcp.listen[80]", "net.tcp.listen[443]", "net.tcp.listen[3306]"]),
        ],
    },
    {
        "file": "20_Template_App_Etcd.xml",
        "template": "Template App Etcd Basic",
        "name": "Template App Etcd Basic",
        "app": "Etcd",
        "description": "Etcd metrics 精简监控，宏 {$ETCD_URL}",
        "macros": [("{ETCD_URL}", "http://127.0.0.1:2379")],
        "items": [
            u("Etcd port 2379", "net.tcp.listen[2379]"),
            u("Etcd process", "proc.num[etcd]"),
            u("Etcd has leader", "etcd[has_leader,{$ETCD_URL}]"),
            u("Etcd leader changes", "etcd[leader_changes,{$ETCD_URL}]", "", 1),
            u("Etcd watchers", "etcd[watchers,{$ETCD_URL}]"),
            u("Etcd db size", "etcd[db_size,{$ETCD_URL}]", "B"),
        ],
        "triggers": [
            ("net.tcp.listen[2379]", "Etcd port 2379 is down on {HOST.NAME}", 4, "listen"),
            ("proc.num[etcd]", "Etcd process is not running on {HOST.NAME}", 4, 0),
        ],
        "graphs": [
            ("Etcd health", ["etcd[has_leader,{$ETCD_URL}]", "etcd[watchers,{$ETCD_URL}]"]),
        ],
    },
]


def fix_macros(spec):
    # Zabbix macros look like {$NAME}; in Python format strings we used {NAME}
    macros = []
    for m, v in spec.get("macros", []):
        if not m.startswith("{") or not m.endswith("}"):
            m = "{$" + m.strip("{}") + "}"
        else:
            # {NGINX_STATUS_URL} -> {$NGINX_STATUS_URL}
            inner = m[1:-1]
            if not inner.startswith("$"):
                m = "{$" + inner + "}"
        macros.append((m, v))
    spec["macros"] = macros
    return spec


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    assert len(TEMPLATES) == 20, len(TEMPLATES)
    index = []
    for spec in TEMPLATES:
        fix_macros(spec)
        path = os.path.join(OUT_DIR, spec["file"])
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build_template(spec))
        index.append((spec["file"], spec["template"], spec.get("description", "")))
        print("wrote", path)

    # catalog markdown fragment
    cat = os.path.join(OUT_DIR, "INDEX.md")
    with open(cat, "w", encoding="utf-8") as fh:
        fh.write("# Templates catalog (20)\n\n")
        fh.write("| # | File | Template | Description |\n")
        fh.write("|---|------|----------|-------------|\n")
        for i, (f, t, d) in enumerate(index, 1):
            fh.write("| {} | `{}` | {} | {} |\n".format(i, f, t, d))
    print("wrote", cat)
    print("OK: {} templates".format(len(TEMPLATES)))


if __name__ == "__main__":
    main()

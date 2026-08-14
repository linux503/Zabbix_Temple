#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 / 通过 API 创建 50 个 Zabbix 主机群组（集合）

用法:
  # 仅生成可导入的 XML（默认）
  python3 create_hostgroups.py --xml > ../hostgroups/hostgroups_50.xml

  # 通过 Zabbix API 创建（已存在则跳过）
  export ZABBIX_URL=http://127.0.0.1/zabbix/api_jsonrpc.php
  export ZABBIX_USER=Admin
  export ZABBIX_PASSWORD=zabbix
  python3 create_hostgroups.py --api
"""

from __future__ import print_function

import argparse
import json
import os
import sys
from datetime import datetime, timezone

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen  # type: ignore


# 50 个常用主机群组（集合），覆盖 OS / 中间件 / 环境 / 业务分层
HOST_GROUPS = [
    # 操作系统 / 基础
    "Linux servers",
    "Windows servers",
    "Network devices",
    "Virtual machines",
    "Physical servers",
    "Containers / K8s nodes",
    "Hypervisors",
    "Storage systems",
    # 中间件 / 数据库
    "MySQL",
    "MongoDB",
    "Redis",
    "PostgreSQL",
    "Nginx",
    "Apache",
    "Tomcat",
    "Kafka",
    "RabbitMQ",
    "Elasticsearch",
    "Memcached",
    "Zookeeper",
    # 环境分层
    "Production",
    "Staging",
    "Testing",
    "Development",
    "DR / Backup site",
    # 业务 / 角色
    "Web frontend",
    "API / Gateway",
    "App backend",
    "Cache layer",
    "Message queue",
    "Database tier",
    "Search / Analytics",
    "CI / CD runners",
    "Jump / Bastion hosts",
    "Monitoring / Zabbix",
    "Logging / ELK",
    # 区域 / 机房
    "IDC-Beijing",
    "IDC-Shanghai",
    "IDC-Guangzhou",
    "Cloud-Aliyun",
    "Cloud-AWS",
    "Cloud-Tencent",
    "Office LAN",
    "DMZ",
    # 其他运维集合
    "Security appliances",
    "Load balancers",
    "CDN edges",
    "IoT / Edge devices",
    "Templates",
    "Discovered hosts",
]

assert len(HOST_GROUPS) == 50, "expected exactly 50 host groups, got {}".format(len(HOST_GROUPS))


def render_xml(groups):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<zabbix_export>",
        "    <version>3.0</version>",
        "    <date>{}</date>".format(now),
        "    <groups>",
    ]
    for name in groups:
        lines.append("        <group>")
        lines.append("            <name>{}</name>".format(name))
        lines.append("        </group>")
    lines.extend(["    </groups>", "</zabbix_export>", ""])
    return "\n".join(lines)


def api_call(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json-rpc"})
    resp = urlopen(req, timeout=30)
    body = json.loads(resp.read().decode("utf-8"))
    if "error" in body:
        raise RuntimeError(body["error"])
    return body["result"]


def create_via_api(groups):
    url = os.environ.get("ZABBIX_URL")
    user = os.environ.get("ZABBIX_USER", "Admin")
    password = os.environ.get("ZABBIX_PASSWORD", "zabbix")
    if not url:
        print("请设置环境变量 ZABBIX_URL", file=sys.stderr)
        sys.exit(1)

    token = api_call(
        url,
        {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {"user": user, "password": password},
            "id": 1,
        },
    )

    existing = api_call(
        url,
        {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {"output": ["name"]},
            "auth": token,
            "id": 2,
        },
    )
    existing_names = {g["name"] for g in existing}

    created = skipped = 0
    for name in groups:
        if name in existing_names:
            print("[skip] {}".format(name))
            skipped += 1
            continue
        api_call(
            url,
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.create",
                "params": {"name": name},
                "auth": token,
                "id": 3,
            },
        )
        print("[ok]   {}".format(name))
        created += 1

    print("完成: 新建 {}，跳过 {}".format(created, skipped))


def main():
    parser = argparse.ArgumentParser(description="Zabbix 50 主机群组工具")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--xml", action="store_true", help="输出可导入 XML（默认）")
    mode.add_argument("--api", action="store_true", help="通过 API 创建群组")
    parser.add_argument("--list", action="store_true", help="仅列出 50 个集合名称")
    args = parser.parse_args()

    if args.list:
        for i, name in enumerate(HOST_GROUPS, 1):
            print("{:02d}. {}".format(i, name))
        return

    if args.api:
        create_via_api(HOST_GROUPS)
        return

    # 默认输出 XML
    sys.stdout.write(render_xml(HOST_GROUPS))


if __name__ == "__main__":
    main()

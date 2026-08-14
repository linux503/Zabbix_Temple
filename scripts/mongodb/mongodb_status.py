#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zabbix MongoDB 监控脚本

用法:
  mongodb_status.py <section> [key] [subkey]
对应 UserParameter: MongoDB.Status[*]

依赖: pymongo
环境变量:
  MONGO_URI   默认 mongodb://127.0.0.1:27017
  MONGO_HOST / MONGO_PORT  (未设置 URI 时使用)
"""

from __future__ import print_function

import os
import sys


def get_client():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("ZBX_NOTSUPPORTED: pymongo not installed", file=sys.stderr)
        sys.exit(1)

    uri = os.environ.get("MONGO_URI")
    if not uri:
        host = os.environ.get("MONGO_HOST", "127.0.0.1")
        port = int(os.environ.get("MONGO_PORT", "27017"))
        uri = "mongodb://{}:{}/".format(host, port)

    return MongoClient(uri, serverSelectionTimeoutMS=3000)


def dig(data, keys):
    cur = data
    for k in keys:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return None
    return cur


def main():
    if len(sys.argv) < 2:
        print("ZBX_NOTSUPPORTED: missing args")
        sys.exit(1)

    parts = [p for p in sys.argv[1:] if p != ""]
    section = parts[0]
    keys = parts[1:]

    try:
        client = get_client()
        # serverStatus 覆盖绝大多数模板指标；process/version/uptime 也在其中
        status = client.admin.command("serverStatus")
    except Exception as exc:
        print("ZBX_NOTSUPPORTED: {}".format(exc))
        sys.exit(1)

    # 顶层简写
    if section in ("process", "version", "uptime") and not keys:
        value = status.get(section)
    else:
        value = dig(status, [section] + keys)

    if value is None:
        print("ZBX_NOTSUPPORTED: path not found")
        sys.exit(1)

    # 布尔转 0/1，便于数值监控项
    if isinstance(value, bool):
        print(1 if value else 0)
    else:
        print(value)


if __name__ == "__main__":
    main()

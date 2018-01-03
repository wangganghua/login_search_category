#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import threading
import redis
import json
rconnection_yz = redis.Redis(host='192.168.2.245', port=6379, db=0)
# 代理ip
redis_key_proxy = "proxy123:iplist"

def cmd():
    proxy = rconnection_yz.srandmember(redis_key_proxy)
    proxyjson = json.loads(proxy)
    ip = proxyjson["ip"]
    print ip
    try:
        rx = rconnection_yz.srem(redis_key_proxy, proxy)
        print rx
    except Exception, e:
        print "err: %s" %e
    print "end"

if __name__ == '__main__':
    cmd()
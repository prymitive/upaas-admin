# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from socket import socket, AF_INET
import json
import logging


log = logging.getLogger(__name__)


def fetch_json_stats(addr, port, timeout=5):
    js = ''
    try:
        s = socket(AF_INET)
        s.settimeout(timeout)
        s.connect((addr, port))
        while True:
            data = s.recv(4096)
            if len(data) < 1:
                break
            js += data
        s.close()
    except Exception, e:
        log.error(u"Couldn't get stats from %s:%s: %s" % (addr, port, e))
    else:
        if js:
            try:
                return json.loads(js)
            except Exception, e:
                log.error(u"Couldn't decode stats JSON data from %s:%s: %s" % (
                    addr, port, e))

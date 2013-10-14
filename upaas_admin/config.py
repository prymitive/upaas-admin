# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config import base


class UPaaSConfig(base.Config):

    schema = {
        "mongodb": {
            "host": base.StringEntry(required=True),
            "port": base.IntegerEntry(default=27017),
            "username": base.StringEntry(),
            "password": base.StringEntry(),
            "database": base.StringEntry(default="upaas"),
        },
        "paths": {
            "workdir": base.FSPathEntry(required=True, must_exist=True),
            "apps": base.FSPathEntry(required=True, must_exist=True),
            "vassals": base.FSPathEntry(required=True, must_exist=True),
        },
        "storage": {
            "handler": base.StringEntry(required=True),
            "settings": base.WildcardEntry(),
        },
        "bootstrap": {
            "timelimit": base.IntegerEntry(required=True),
            "env": base.DictEntry(value_type=unicode),
            "commands": base.ScriptEntry(required=True),
            "maxage": base.IntegerEntry(default=7),
            "packages": base.ListEntry(value_type=basestring),
        },
        "commands": {
            "timelimit": base.IntegerEntry(required=True),
            "install": {
                "env": base.DictEntry(value_type=unicode),
                "cmd": base.StringEntry(required=True),
            },
            "uninstall": {
                "env": base.DictEntry(value_type=unicode),
                "cmd": base.StringEntry(required=True),
            },
        },
        "apps": {
            "uid": base.StringEntry(required=True),
            "gid": base.StringEntry(required=True),
            "home": base.StringEntry(required=True),
            "domain": base.StringEntry(default="upaas.local"),
            "tcp": {
                "port_min": base.IntegerEntry(required=True),
                "port_max": base.IntegerEntry(required=True),
            }
        },
        "defaults": {
            "budget": {
                "apps_count": base.IntegerEntry(required=True),
                "worker_limit": base.IntegerEntry(required=True),
                "memory_limit": base.IntegerEntry(required=True),
            }
        },
        "admin": {
            "secretkey": base.StringEntry(required=True),
            "debug": base.BooleanEntry(default=False),
            "domains": base.ListEntry(value_type=basestring),
            "log": base.FSPathEntry(must_exist=False,
                                    default="/tmp/upaas_admin.log"),
        },
        "interpreters": base.WildcardEntry(),
    }


def load_main_config():
    return base.load_config(UPaaSConfig, 'upaas.yml')

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.config import base
from upaas.compat import unicode


class InterpreterConfig(base.Config):

    schema = {
        "env": base.DictEntry(value_type=unicode),
        "uwsgi": {
            "plugin": base.StringEntry(),
            "template": base.FSPathEntry(),
            "vars": base.DictEntry(),
        },
        "settings": base.DictEntry(value_type=unicode),
        "packages": base.ListEntry(value_type=unicode),
        "actions": {
            "setup": {
                "interpreter": base.ScriptEntry(),
                "main": base.ScriptEntry(),
            }
        }
    }


class FeatureConfig(base.Config):

    schema = {
        "handler": base.StringEntry(required=True),
        "enabled": base.BooleanEntry(default=False),
        "settings": base.WildcardEntry(),
    }


class UPaaSConfig(base.Config):

    schema = {
        "mongodb": {
            "uri": base.StringEntry(),
            "host": base.StringEntry(default='localhost'),
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
            "packages": base.ListEntry(value_type=unicode),
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
            "domains": {
                "system": base.StringEntry(required=True,
                                           default="localdomain"),
                "validation": base.BooleanEntry(default=True),
            },
            "tcp": {
                "port_min": base.IntegerEntry(required=True),
                "port_max": base.IntegerEntry(required=True),
            },
            "uwsgi": {
                "safe_options": base.ListEntry(value_type=unicode),
            },
            "graphite": {
                "carbon": base.ListEntry(value_type=unicode),
                "render_url": base.StringEntry(),
                "timeout": base.IntegerEntry(default=3),
                "frequency": base.IntegerEntry(default=60),
                "max_retry": base.IntegerEntry(default=1),
                "retry_delay": base.IntegerEntry(default=7),
                "root": base.StringEntry(default="uwsgi"),
            },
            "features": base.ConfigDictEntry(FeatureConfig),
        },
        "defaults": {
            "limits": {
                "running_apps": base.IntegerEntry(required=True, min_value=0),
                "workers": base.IntegerEntry(required=True, min_value=0),
                "memory_per_worker": base.IntegerEntry(required=True,
                                                       min_value=16),
                "packages_per_app": base.IntegerEntry(required=True,
                                                      min_value=2),
                "max_log_size": base.IntegerEntry(required=True, min_value=1),
            }
        },
        "admin": {
            "secretkey": base.StringEntry(required=True),
            "loglevel": base.StringEntry(default='info'),
            "debug": base.BooleanEntry(default=False),
            "domains": base.ListEntry(value_type=unicode),
            "smtp": {
                "host": base.StringEntry(default='localhost', required=True),
                "port": base.IntegerEntry(default=25, required=True),
                "tls": base.BooleanEntry(default=False),
                "username": base.StringEntry(),
                "password": base.StringEntry(),
                "sender": base.StringEntry(default='no-reply@localhost',
                                           required=True),
            }
        },
        "interpreters": {
            "env": base.DictEntry(),
            "uwsgi": {
                "template": base.StringEntry(required=True),
            },
            "actions": {
                "setup": {
                    "system": base.ScriptEntry(),
                    "finalize": base.ScriptEntry(),
                }
            },
            "ruby": base.ConfigDictEntry(InterpreterConfig),
            "php": base.ConfigDictEntry(InterpreterConfig),
            "python": base.ConfigDictEntry(InterpreterConfig),
        }
    }


def load_main_config():
    return base.load_config(UPaaSConfig, 'upaas.yml')

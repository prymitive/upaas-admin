# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.core.cache import cache

from upaas.config.main import UPaaSConfig, load_main_config


def cached_main_config():
    """
    Returns cached copy of UPaaS main config.
    """
    key = '__upaas.config.main'
    config_data = cache.get(key)
    if config_data:
        main_config = UPaaSConfig.from_string(config_data)
    else:
        main_config = load_main_config()
        cache.set(key, main_config.dump_string(), 60)
    return main_config

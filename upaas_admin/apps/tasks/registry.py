# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from django.utils.importlib import import_module

REGISTERED_TASKS = {}
LOADING_TASKS = False


log = logging.getLogger(__name__)


def register(cls):
    REGISTERED_TASKS[cls.__name__] = cls
    return cls


def registered_tasks():
    global REGISTERED_TASKS
    return REGISTERED_TASKS


def find_task_class(name):
    global REGISTERED_TASKS
    return REGISTERED_TASKS.get(name)


def tasks_autodiscover():
    """
    Auto-discover INSTALLED_APPS ajax.py modules and fail silently when
    not present. Copied from dajaxice.
    """
    global LOADING_TASKS
    if LOADING_TASKS:
        return
    LOADING_TASKS = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:

        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        try:
            imp.find_module('tasks', app_path)
        except ImportError:
            continue

        log.debug(u"Loading tasks module: %s.tasks" % app)
        import_module("%s.tasks" % app)

    LOADING_TASKS = False
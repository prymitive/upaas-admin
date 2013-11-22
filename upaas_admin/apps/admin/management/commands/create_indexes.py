# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import sys
import imp
import inspect
import logging

from mongoengine import Document

from django.core.management.base import BaseCommand
from django.utils.importlib import import_module
from django.conf import settings


log = logging.getLogger("create_indexes")


class Command(BaseCommand):

    help = 'Create missing MongoDB indexes'

    def handle(self, *args, **options):
        models = {}
        for app in settings.INSTALLED_APPS:

            if not app.startswith('upaas_admin.'):
                continue

            try:
                app_path = import_module(app).__path__
            except AttributeError:
                continue

            try:
                imp.find_module('models', app_path)
            except ImportError:
                continue

            log.debug(u"Loading models from: %s.models" % app)
            module = import_module("%s.models" % app)

            for name, obj in inspect.getmembers(sys.modules[module.__name__],
                                                predicate=inspect.isclass):
                if issubclass(obj, Document):
                    log.debug(u"Found model '%s'" % name)
                    models[obj.__name__] = obj

        for model in models.values():
            log.info(u"Checking %s" % model.__name__)
            if model._meta and model._meta.get('indexes') and \
                    not model._meta.get('abstract'):
                model.ensure_indexes()

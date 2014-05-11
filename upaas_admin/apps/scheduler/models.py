# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from mongoengine import (Document, EmbeddedDocument, QuerySetManager,
                         IntField, ReferenceField, EmbeddedDocumentField,
                         ListField, signals)

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


log = logging.getLogger(__name__)


class UserLimits(Document):
    """
    How much resources can user apps consume.
    """
    user = ReferenceField('User', dbref=False, unique=True, required=True)

    running_apps = IntField(verbose_name=_('running applications limit'),
                            min_value=0)
    packages_per_app = IntField(verbose_name=_('stored packages limit'),
                                min_value=2)
    workers = IntField(verbose_name=_('total running workers limit'),
                       min_value=0)
    memory_per_worker = IntField(verbose_name=_('memory per worker limit'),
                                 min_value=16)
    max_log_size = IntField(verbose_name=_('log file size limit'), min_value=1)

    meta = {
        'indexes': ['user'],
    }

    _default_manager = QuerySetManager()

    limit_fields = ['running_apps', 'packages_per_app', 'workers',
                    'memory_per_worker', 'max_log_size']

    @classmethod
    def get_default_limits(cls):
        return settings.UPAAS_CONFIG.dump()['defaults']['limits']

    @property
    def safe_id(self):
        return str(self.id)


class BackendRunPlanSettings(EmbeddedDocument):
    """
    Application instance settings for given backend.
    """
    backend = ReferenceField('BackendServer', dbref=False)
    package = ReferenceField('Package', dbref=False, required=True)
    socket = IntField(required=True)
    stats = IntField(required=True)
    workers_min = IntField(required=True)
    workers_max = IntField(required=True)


class ApplicationRunPlan(Document):
    """
    Where should application run and how much resources can given app consume.
    """
    application = ReferenceField('Application', dbref=False, required=True,
                                 unique=True)
    backends = ListField(EmbeddedDocumentField(BackendRunPlanSettings))
    workers_min = IntField(required=True, min_value=1, default=1,
                           verbose_name=_('minimum number of workers'))
    workers_max = IntField(required=True, min_value=1, default=1,
                           verbose_name=_('maximum number of workers'))
    memory_per_worker = IntField(required=True, min_value=16,
                                 verbose_name=_('memory per worker limit'))
    max_log_size = IntField(required=True, min_value=1, default=100,
                            verbose_name=_('log file size limit'))

    _default_manager = QuerySetManager()

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        log.debug(_("Pre delete signal on run_plan for {name}").format(
            name=document.application.name))
        document.application.update(unset__run_plan=True)

    def backend_settings(self, backend):
        for backend_conf in self.backends:
            if backend_conf.backend == backend:
                return backend_conf

    def remove_backend_settings(self, backend):
        self.__class__.objects(id=self.id).update_one(
            pull__backends__backend=backend)

    def append_backend_settings(self, backend_conf):
        self.__class__.objects(id=self.id).update_one(
            push__backends=backend_conf)

    def replace_backend_settings(self, backend, backend_conf, **kwargs):
        self.remove_backend_settings(backend)
        data = backend_conf._data
        data.update(kwargs)
        self.append_backend_settings(BackendRunPlanSettings(**data))
        self.reload()
        return self.backend_settings(backend)

    def is_valid(self):
        total_min = 0
        total_max = 0
        for backend_conf in self.backends:
            if not backend_conf.backend.is_enabled:
                log.warning(_(
                    "Backend {backend} is disable, run plan for {name} is no "
                    "longer valid").format(
                        backend=backend_conf.backend.name,
                        name=self.application.name))
                return False
            total_min += backend_conf.workers_min
            total_max += backend_conf.workers_max
        if total_min != self.workers_min or total_max != self.workers_max:
            log.warning(_(
                "Allocated workers count is different then expected, run plan"
                " for {name} is invalid").format(name=self.application.name))
            return False
        return True


signals.pre_delete.connect(ApplicationRunPlan.pre_delete,
                           sender=ApplicationRunPlan)

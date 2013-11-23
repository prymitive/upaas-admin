# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import (Document, EmbeddedDocument, QuerySetManager,
                         IntField, ReferenceField, EmbeddedDocumentField,
                         ListField)

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class UserLimits(Document):
    """
    How much resources can user apps consume.
    """
    user = ReferenceField('User', dbref=False, unique=True, required=True)

    running_apps = IntField(verbose_name=_('running applications limit'))
    packages_per_app = IntField(verbose_name=_('stored packages limit'))
    workers = IntField(verbose_name=_('total running workers limit'))
    memory_per_worker = IntField(verbose_name=_('memory per worker limit'))

    meta = {
        'indexes': ['user'],
    }

    _default_manager = QuerySetManager()

    @classmethod
    def get_default_limits(cls):
        return settings.UPAAS_CONFIG.dump()['defaults']['limits']


class BackendRunPlanSettings(EmbeddedDocument):
    """
    Application instance settings for given backend.
    """
    backend = ReferenceField('BackendServer', dbref=False)
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
    memory_per_worker = IntField(required=True,
                                 verbose_name=_('memory per worker limit'))

    _default_manager = QuerySetManager()

    def backend_settings(self, backend):
        for backend_conf in self.backends:
            if backend_conf.backend == backend:
                return backend_conf

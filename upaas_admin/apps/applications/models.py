# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime
import logging

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from upaas_admin.apps.applications.tasks import build_package as \
    build_package_task


log = logging.getLogger(__name__)


class Package(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    metadata = StringField(help_text=_('Application metadata'))

    bytes = LongField(required=True)
    checksum = StringField(required=True)

    distro_name = StringField(required=True)
    distro_version = StringField(required=True)
    distro_arch = StringField(required=True)


class Application(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=100, unique_with='owner',
                       verbose_name=_('name'), help_text=_('Application name'))
    owner = ReferenceField('User', reverse_delete_rule=DENY, dbref=False,
                           required=True)
    metadata = StringField(help_text=_('Application metadata'))
    current_package = ReferenceField(Package, reverse_delete_rule=CASCADE,
                                     dbref=False)
    packages = ListField(
        ReferenceField(Package, reverse_delete_rule=CASCADE, dbref=False))

    meta = {
        'indexes': [
            {'fields': ['name', 'owner']}
        ]
    }

    def build_package(self, force_fresh=False):
        task = build_package_task.apply_async((self.metadata,),
                                              {'force_fresh': force_fresh},
                                              queue='builder')
        log.info("Build task for app '%s' queued with id '%s'" % (
            self.name, task.task_id))
        return task.task_id

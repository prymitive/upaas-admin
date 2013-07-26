# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime
import logging

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from celery.execute import send_task

from upaas import utils
from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig

from upaas_admin.apps.users.models import User


log = logging.getLogger(__name__)


class Package(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    metadata = StringField(help_text=_('Application metadata'))

    interpreter_name = StringField(required=True)
    interpreter_version = StringField(required=True)

    parent = StringField()
    filename = StringField(required=True)
    bytes = LongField(required=True)
    checksum = StringField(required=True)

    distro_name = StringField(required=True)
    distro_version = StringField(required=True)
    distro_arch = StringField(required=True)

    meta = {
        'indexes': [
            {'fields': ['filename']}
        ],
        'ordering': ['date_created'],
    }


class Application(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=100, unique_with='owner',
                       verbose_name=_('name'))
    owner = ReferenceField(User, reverse_delete_rule=DENY, dbref=False,
                           required=True)
    metadata = StringField(verbose_name=_('Application metadata'))
    current_package = ReferenceField(Package, reverse_delete_rule=CASCADE,
                                     dbref=False)
    packages = ListField(
        ReferenceField(Package, reverse_delete_rule=CASCADE, dbref=False))

    meta = {
        'indexes': [
            {'fields': ['name', 'owner']}
        ],
        'ordering': ['name'],
    }

    @property
    def metadata_config(self):
        if self.metadata:
            return MetadataConfig.from_string(self.metadata)
        return {}

    @property
    def interpreter_name(self):
        """
        Will return interpreter from current package metadata.
        If no package was built interpreter will be fetched from app metadata.
        If app has no metadata it will return None.
        """
        if self.current_package:
            return self.current_package.interpreter_name
        else:
            try:
                return self.metadata_config.interpreter.type
            except KeyError:
                return None

    @property
    def interpreter_version(self):
        """
        Will return interpreter version from current package metadata.
        If no package was built interpreter will be fetched from app metadata.
        If app has no metadata it will return None.
        """
        if self.current_package:
            return self.current_package.interpreter_version
        elif self.metadata:
            #FIXME maybe its better to load main config at startup?
            config = load_main_config()
            return utils.select_best_version(config, self.metadata_config)

    def build_package(self, force_fresh=False):
        system_filename = None
        if not force_fresh and self.current_package:
            system_filename = self.current_package.filename
        task = send_task('upaas_admin.apps.applications.tasks.build_package',
                         (self.metadata,),
                         {'app_id': self.id,
                          'system_filename': system_filename},
                         queue='builder')
        log.info("Build task for app '%s' queued with id '%s'" % (
            self.name, task.task_id))
        return task.task_id

    def start_application(self):
        if self.current_package:
            task = send_task(
                'upaas_admin.apps.applications.tasks.start_application',
                (self.metadata, self.current_package.id), queue='builder')
            log.info("Start task for app '%s' queued with id '%s'" % (
                self.name, task.task_id))
            return task.task_id

    def generate_uwsgi_config(self, backend):
        pass

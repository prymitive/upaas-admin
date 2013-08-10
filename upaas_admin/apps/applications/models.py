# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import datetime
import logging

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from celery.execute import send_task

from upaas import utils
from upaas.config.base import UPAAS_CONFIG_DIRS
from upaas.config.metadata import MetadataConfig

from upaas_admin.apps.users.models import User
from upaas_admin.apps.servers.models import RouterServer
from upaas_admin.apps.tasks.models import Task
from upaas_admin.config import cached_main_config


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

    @property
    def safe_id(self):
        return str(self.id)

    @property
    def metadata_config(self):
        if self.metadata:
            return MetadataConfig.from_string(self.metadata)
        return {}

    @property
    def application(self):
        return Application.objects(packages=self.id).first()

    def generate_uwsgi_config(self, backend):
        """
        :param backend: BackendServer instance for which we generate config
        """

        def _load_template(path):
            for search_path in UPAAS_CONFIG_DIRS:
                template_path = os.path.join(search_path, path)
                if os.path.exists(template_path):
                    f = open(template_path)
                    ret = f.read().splitlines()
                    f.close()
                    return ret

        config = cached_main_config()

        base_template = config.interpreters['uwsgi']['template']

        template = None
        try:
            template = config.interpreters[self.interpreter_name]['any'][
                'uwsgi']['template']
        except (AttributeError, KeyError):
            pass
        try:
            template = config.interpreters[self.interpreter_name][
                self.interpreter_version]['uwsgi']['template']
        except (AttributeError, KeyError):
            pass

        vars = {
            'namespace': os.path.join(config.paths.apps, self.safe_id),
            'chdir': config.apps.home,
            'socket': '%s:0' % backend.ip,
            'uid': config.apps.uid,
            'gid': config.apps.gid,
            'app_name': self.application.name,
            'app_id': self.application.safe_id,
            'pkg_id': self.safe_id,
        }
        try:
            vars.update(config.interpreters[self.interpreter_name]['any'][
                'uwsgi']['vars'])
        except (AttributeError, KeyError):
            pass
        try:
            vars.update(config.interpreters[self.interpreter_name][
                self.interpreter_version]['uwsgi']['vars'])
        except (AttributeError, KeyError):
            pass

        envs = {}
        try:
            envs.update(config.interpreters[self.interpreter_name]['any'][
                'env'])
        except (AttributeError, KeyError):
            pass
        try:
            envs.update(config.interpreters[self.interpreter_name][
                self.interpreter_version]['env'])
        except (AttributeError, KeyError):
            pass

        plugin = None
        try:
            plugin = config.interpreters[self.interpreter_name]['any'][
                'uwsgi']['plugin']
        except (AttributeError, KeyError):
            pass
        try:
            plugin = config.interpreters[self.interpreter_name][
                self.interpreter_version]['uwsgi']['plugin']
        except (AttributeError, KeyError):
            pass

        options = ['[uwsgi]']

        options.append('\n# starting uWSGI config variables list')
        for key, value in vars.items():
            options.append('var_%s = %s' % (key, value))

        options.append('\n# starting ENV variables list')
        for key, value in envs.items():
            options.append('env = %s=%s' % (key, value))

        options.append('\n# starting base template')
        options.extend(_load_template(base_template))

        options.append('\n# starting interpreter plugin')
        if plugin:
            options.append('plugin = %s' % plugin)

        options.append('\n# starting interpreter template')
        options.extend(_load_template(template))

        options.append('\n# starting subscriptions block')
        for router in RouterServer.objects(is_enabled=True):
            options.append('subscribe2 = server=%s:%d,key=%s' % (
                router.private_ip, router.subscription_port,
                self.application.system_domain))
            for domain in self.application.domains:
                options.append('subscribe2 = server=%s:%d,key=%s' % (
                    router.private_ip, router.subscription_port, domain))

        options.append('\n')
        return options


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
    domains = ListField(StringField)

    meta = {
        'indexes': [
            {'fields': ['name', 'owner']}
        ],
        'ordering': ['name'],
    }

    @property
    def safe_id(self):
        return str(self.id)

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
            config = cached_main_config()
            return utils.select_best_version(config, self.metadata_config)

    @property
    def system_domain(self):
        """
        Returns automatic system domain for this application.
        """
        config = cached_main_config()
        return '%s.%s' % (self.safe_id, config.apps.domain)

    def build_package(self, force_fresh=False):
        system_filename = None
        title = _("Building new fresh package")
        if not force_fresh and self.current_package:
            system_filename = self.current_package.filename
            title = _("Building new package")
        task = send_task('upaas_admin.apps.applications.tasks.build_package',
                         (self.metadata,),
                         {'app_id': self.id,
                          'system_filename': system_filename},
                         queue='builder')
        log.info("Build task for app '%s' queued with id '%s'" % (
            self.name, task.task_id))
        task_link = Task(task_id=task.task_id, title=title, application=self)
        task_link.save()
        return task.task_id

    def start_application(self):
        if self.current_package:
            task = send_task(
                'upaas_admin.apps.applications.tasks.start_application',
                (self.metadata, self.current_package.id), queue='builder')
            log.info("Start task for app '%s' queued with id '%s'" % (
                self.name, task.task_id))
            return task.task_id

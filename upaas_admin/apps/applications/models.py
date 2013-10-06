# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

import os
import datetime
import logging
import tempfile
import shutil
import time
from copy import deepcopy

from mongoengine import (Document, DateTimeField, StringField, LongField,
                         ReferenceField, ListField, CASCADE, QuerySetManager)

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from upaas import utils
from upaas import tar
from upaas.config.base import UPAAS_CONFIG_DIRS
from upaas.config.metadata import MetadataConfig
from upaas.storage.utils import find_storage_handler
from upaas.storage.exceptions import StorageError
from upaas import processes

from upaas_admin.apps.servers.models import RouterServer
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.scheduler.base import select_best_backend
from upaas_admin.apps.servers.constants import PortsNames
from upaas_admin.apps.tasks.models import Task


log = logging.getLogger(__name__)


class Package(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    metadata = StringField(help_text=_('Application metadata'))
    application = ReferenceField('Application', dbref=False, required=True)

    interpreter_name = StringField(required=True)
    interpreter_version = StringField(required=True)

    parent = StringField()
    filename = StringField(required=True)
    bytes = LongField(required=True)
    checksum = StringField(required=True)
    builder = StringField(required=True)

    distro_name = StringField(required=True)
    distro_version = StringField(required=True)
    distro_arch = StringField(required=True)

    meta = {
        'indexes': ['filename'],
        'ordering': ['-date_created'],
    }

    _default_manager = QuerySetManager()

    @property
    def safe_id(self):
        return str(self.id)

    @property
    def metadata_config(self):
        if self.metadata:
            return MetadataConfig.from_string(self.metadata)
        return {}

    @property
    def upaas_config(self):
        return settings.UPAAS_CONFIG

    @property
    def package_path(self):
        """
        Unpacked package directory path
        """
        return os.path.join(settings.UPAAS_CONFIG.paths.apps, self.safe_id)

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

        # so it won't change while generating configuration
        config = deepcopy(self.upaas_config)

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

        ports_data = backend.application_ports(self.application)
        ports = {}
        needs_update = False
        if ports_data and PortsNames.socket in ports_data.ports:
            ports[PortsNames.socket] = ports_data.ports[PortsNames.socket]
        else:
            ports[PortsNames.socket] = backend.find_free_port()
            needs_update = True
        if ports_data and PortsNames.stats in ports_data.ports:
            ports[PortsNames.stats] = ports_data.ports[PortsNames.stats]
        else:
            ports[PortsNames.stats] = backend.find_free_port()
            needs_update = True
        if needs_update:
            backend.set_application_ports(self.application, ports)

        log.info(u"Using socket=%d and stats=%d for '%s'" % (
            ports[PortsNames.socket], ports[PortsNames.stats],
            self.application.name))

        vars = {
            'namespace': self.package_path,
            'chdir': config.apps.home,
            'socket': '%s:%d' % (backend.ip, ports[PortsNames.socket]),
            'stats': '%s:%d' % (backend.ip, ports[PortsNames.stats]),
            'uid': config.apps.uid,
            'gid': config.apps.gid,
            'app_name': self.application.name,
            'app_id': self.application.safe_id,
            'pkg_id': self.safe_id,
            'max_workers': self.application.run_plan.worker_limit,
            'max_memory': self.application.run_plan.memory_limit * 1024 * 1024
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

    def save_vassal_config(self, backend):
        log.info(u"Generating uWSGI vassal configuration")
        options = self.generate_uwsgi_config(backend)
        log.info(u"Saving vassal configuration to "
                 u"'%s'" % self.application.vassal_path)
        with open(self.application.vassal_path, 'w') as vassal:
            vassal.write('\n'.join(options))
        log.info(u"Vassal saved")

    def unpack(self):
        upaas_config = self.upaas_config

        # directory is encoded into string to prevent unicode errors
        directory = tempfile.mkdtemp(dir=upaas_config.paths.workdir,
                                     prefix="upaas_package_").encode("utf-8")

        storage = find_storage_handler(upaas_config)
        if not storage:
            log.error(u"Storage handler '%s' not "
                      u"found" % upaas_config.storage.handler)

        workdir = os.path.join(directory, "system")
        pkg_path = os.path.join(directory, self.filename)

        if os.path.exists(self.package_path):
            log.error(u"Package directory already exists: "
                      u"%s" % self.package_path)
            raise UnpackError(u"Package directory already exists")

        log.info(u"Fetching package '%s'" % self.filename)
        try:
            storage.get(self.filename, pkg_path)
        except StorageError:
            log.error(u"Storage error while fetching package "
                      u"'%s'" % self.filename)
            utils.rmdirs(directory)
            raise StorageError(u"Can't fetch package '%s' from "
                               u"storage" % self.filename)

        log.info(u"Unpacking package")
        os.mkdir(workdir, 0755)
        if not tar.unpack_tar(pkg_path, workdir):
            log.error(u"Error while unpacking package to '%s'" % workdir)
            utils.rmdirs(directory)
            raise UnpackError(u"Error during package unpack")

        log.info(u"Package unpacked, moving into '%s'" % self.package_path)
        try:
            shutil.move(workdir, self.package_path)
        except shutil.Error, e:
            log.error(u"Error while moving unpacked package to final "
                      u"destination: %s" % e)
            utils.rmdirs(directory, self.package_path)
            raise UnpackError(u"Can't move to final directory "
                              u"'%s'" % self.package_path)
        log.info(u"Package moved")
        utils.rmdirs(directory)

    def cleanup_application_packages(self):
        """
        Remove all but current unpacked packages
        """
        log.info(u"Cleaning old packages for '%s'" % self.application.name)
        for oldpkg in self.application.packages:
            if oldpkg.id == self.id:
                # skip current package!
                continue
            if os.path.isdir(oldpkg.package_path):
                log.info(u"Removing package directory "
                         u"'%s'" % oldpkg.package_path)

                # if there are running pids inside package dir we will need to
                # wait this should only happen during upgrade, when we need to
                # wait for app to reload into new package dir
                pids = processes.directory_pids(oldpkg.package_path)
                while pids:
                    log.info(u"Waiting for %d pid(s) in %s to terminate" % (
                        len(pids), oldpkg.package_path))
                    time.sleep(2)
                    pids = processes.directory_pids(oldpkg.package_path)

                try:
                    processes.kill_and_remove_dir(oldpkg.package_path)
                except OSError, e:
                    log.error(u"Exception during package directory cleanup: "
                              u"%s" % e)


class Application(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=100, unique_with='owner',
                       verbose_name=_('name'))
    # FIXME reverse_delete_rule=DENY for owner
    owner = ReferenceField('User', dbref=False, required=True)
    metadata = StringField(verbose_name=_('Application metadata'))
    current_package = ReferenceField(Package, reverse_delete_rule=CASCADE,
                                     dbref=False, required=False)
    packages = ListField(
        ReferenceField(Package, reverse_delete_rule=CASCADE, dbref=False))
    domains = ListField(StringField)  # FIXME uniqness

    _default_manager = QuerySetManager()

    meta = {
        'indexes': [
            {'fields': ['name', 'owner'], 'unique': True}
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
    def upaas_config(self):
        return settings.UPAAS_CONFIG

    @property
    def vassal_path(self):
        """
        Application vassal config file path.
        """
        return os.path.join(self.upaas_config.paths.vassals,
                            '%s.ini' % self.safe_id)

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
            return utils.select_best_version(self.upaas_config,
                                             self.metadata_config)

    @property
    def system_domain(self):
        """
        Returns automatic system domain for this application.
        """
        return '%s.%s' % (self.safe_id, self.upaas_config.apps.domain)

    @property
    def run_plan(self):
        """
        Application run plan if it is present, None otherwise.
        """
        return ApplicationRunPlan.objects(application=self).first()

    @property
    def can_start(self):
        """
        Returns True only if package is not started but it can be.
        """
        return bool(self.current_package and self.run_plan is None)

    def get_absolute_url(self):
        return reverse('app_details', args=[self.safe_id])

    def build_package(self, force_fresh=False):
        system_filename = None
        title = _("Building new fresh package for") + " " + self.name
        if not force_fresh and self.current_package:
            system_filename = self.current_package.filename
            title = _("Building new package for") + " " + self.name
        task = Task.put('BuildPackageTask', title=title, application=self,
                        metadata=self.metadata,
                        system_filename=system_filename)
        log.info(u"Created start task: %s" % task.safe_id)

    def start_application(self):
        if self.current_package:
            run_plan = self.run_plan
            if not run_plan:
                log.error(u"Trying to start '%s' without run plan" % self.name)
                return

            backend = select_best_backend(run_plan.backends)
            if not backend:
                log.error(u"Can't start '%s', no backend "
                          u"available" % self.name)
                return

            log.info(u"Setting backend '%s' in '%s' run plan" % (backend.name,
                                                                 self.name))

            run_plan.backends += [backend]
            run_plan.save()

            task = Task.put('StartPackageTask',
                            title=u'Starting application %s' % self.name,
                            backend=backend, application=self,
                            package=self.current_package)
            log.info(u"Created start task: %s" % task.safe_id)

    def stop_application(self):
        if self.current_package:
            if not self.run_plan:
                return
            for backend in self.run_plan.backends:
                task = Task.put('StopPackageTask',
                                title=u'Stooping application %s' % self.name,
                                backend=backend, application=self,
                                package=self.current_package)
                log.info(u"Created stop task: %s" % task.safe_id)
            #TODO rewrite for task group (?)

    def update_application(self):
        if self.current_package:
            if not self.run_plan:
                return
            for backend in self.run_plan.backends:
                task = Task.put('UpdatePackageTask',
                                title=u'Updating application %s' % self.name,
                                backend=backend, application=self,
                                package=self.current_package)
                log.info(u"Created update task: %s" % task.safe_id)

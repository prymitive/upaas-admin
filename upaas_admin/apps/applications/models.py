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
from upaas.checksum import calculate_file_sha256, calculate_string_sha256
from upaas.config.base import UPAAS_CONFIG_DIRS
from upaas.config.metadata import MetadataConfig
from upaas.storage.utils import find_storage_handler
from upaas.storage.exceptions import StorageError
from upaas import processes

from upaas_admin.apps.servers.models import RouterServer
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.scheduler.base import select_best_backends
from upaas_admin.apps.servers.constants import PortsNames
from upaas_admin.apps.tasks.models import Task
from upaas_admin.apps.tasks.base import VirtualTask
from upaas_admin.apps.tasks.constants import TaskStatus, ACTIVE_TASK_STATUSES


log = logging.getLogger(__name__)


class Package(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    metadata = StringField(help_text=_('Application metadata'))
    application = ReferenceField('Application', dbref=False, required=True)

    interpreter_name = StringField(required=True)
    interpreter_version = StringField(required=True)

    parent = StringField()
    filename = StringField()
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

    def generate_uwsgi_config(self, backend_conf):
        """
        :param backend_conf: BackendRunPlanSettings instance for which we
                             generate config
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

        max_memory = backend_conf.workers
        max_memory *= self.application.run_plan.memory_per_worker
        max_memory *= 1024 * 1024

        vars = {
            'namespace': self.package_path,
            'chdir': config.apps.home,
            'socket': '%s:%d' % (backend_conf.backend.ip, backend_conf.socket),
            'stats': '%s:%d' % (backend_conf.backend.ip, backend_conf.stats),
            'uid': config.apps.uid,
            'gid': config.apps.gid,
            'app_name': self.application.name,
            'app_id': self.application.safe_id,
            'pkg_id': self.safe_id,
            'max_workers': self.application.run_plan.worker_limit,
            'max_memory': max_memory,
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

        # enable cheaper mode if we have multiple workers
        if self.application.run_plan.worker_limit > 1:
            options.append('\n# enabling cheaper mode')
            options.append('cheaper = 1')

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
        options = u"\n".join(self.generate_uwsgi_config(backend))

        if os.path.exists(self.application.vassal_path):
            current_hash = calculate_file_sha256(self.application.vassal_path)
            new_hash = calculate_string_sha256(options)
            if current_hash == new_hash:
                log.info(u"Vassal is present and valid, skipping rewrite")
                return

        log.info(u"Saving vassal configuration to "
                 u"'%s'" % self.application.vassal_path)
        with open(self.application.vassal_path, 'w') as vassal:
            vassal.write(options)
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
            {'fields': ['name', 'owner'], 'unique': True},
            {'fields': ['packages']}
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

    @property
    def tasks(self):
        """
        List of all tasks for this application.
        """
        return Task.find('ApplicationTask', application=self)

    @property
    def active_tasks(self):
        """
        List of all active (pending or running) application tasks.
        """
        return self.tasks.filter(status__in=ACTIVE_TASK_STATUSES)

    @property
    def pending_tasks(self):
        """
        List of all pending tasks for this application.
        """
        return self.tasks.filter(status=TaskStatus.pending)

    @property
    def running_tasks(self):
        """
        List of all running tasks for this application.
        """
        return self.tasks.filter(status=TaskStatus.running)

    @property
    def build_tasks(self):
        """
        List of all build tasks for this application.
        """
        return Task.find('BuildPackageTask', application=self)

    @property
    def active_build_tasks(self):
        """
        List of all active (pending or running) build tasks for this
        application.
        """
        return self.build_tasks.filter(status__in=ACTIVE_TASK_STATUSES)

    @property
    def pending_build_tasks(self):
        """
        List of pending build tasks for this application.
        """
        return self.build_tasks.filter(status=TaskStatus.pending)

    @property
    def running_build_tasks(self):
        """
        Returns list of running build tasks for this application.
        """
        return self.build_tasks.filter(status=TaskStatus.running)

    def get_absolute_url(self):
        return reverse('app_details', args=[self.safe_id])

    def build_package(self, force_fresh=False):
        if self.pending_build_tasks:
            log.info(_(u"Application {name} is already queued for "
                       u"building").format(name=self.name))
        else:
            system_filename = None
            if not force_fresh and self.current_package:
                system_filename = self.current_package.filename
            task = Task.put('BuildPackageTask', application=self,
                            metadata=self.metadata,
                            system_filename=system_filename)
            return task

    def start_application(self):
        if self.current_package:
            run_plan = self.run_plan
            if not run_plan:
                log.error(u"Trying to start '%s' without run plan" % self.name)
                return

            backends = select_best_backends(run_plan)
            if not backends:
                log.error(_(u"Can't start '{name}', no backend "
                            u"available").format(name=self.name))
                run_plan.delete()
                return

            kwargs = {}
            if len(backends) > 1:
                vtask = VirtualTask(
                    title=_(u"Starting application {name}").format(
                        name=self.name))
                vtask.save()
                kwargs['parent'] = vtask

            run_plan.backends = backends
            run_plan.save()

            for backend_conf in backends:
                log.info(_(u"Set backend '{backend}' in '{name}' run "
                           u"plan").format(backend=backend_conf.backend.name,
                                           name=self.name))
                Task.put('StartPackageTask', backend=backend_conf.backend,
                         application=self, package=self.current_package,
                         **kwargs)

    def stop_application(self):
        if self.current_package:
            if not self.run_plan:
                return
            if self.run_plan and not self.run_plan.backends:
                # no backends in run plan, just delete it
                self.run_plan.delete()
                return

            kwargs = {}
            if len(self.run_plan.backends) > 1:
                vtask = VirtualTask(
                    title=_(u"Stopping application {name}").format(
                        name=self.name))
                vtask.save()
                kwargs['parent'] = vtask

            for backend_conf in self.run_plan.backends:
                Task.put('StopPackageTask', backend=backend_conf.backend,
                         application=self, package=self.current_package,
                         **kwargs)

    def upgrade_application(self):
        if self.current_package:
            if not self.run_plan:
                return

            kwargs = {}
            if len(self.run_plan.backends) > 1:
                vtask = VirtualTask(
                    title=_(u"Upgrading application {name}").format(
                        name=self.name))
                vtask.save()
                kwargs['parent'] = vtask

            #TODO add wait for subscription
            for backend_conf in self.run_plan.backends:
                Task.put('UpgradePackageTask', backend=backend_conf.backend,
                         application=self, package=self.current_package,
                         **kwargs)

    def update_application(self):
        if self.run_plan:

            run_plan = self.run_plan

            current_backends = [bc.backend for bc in run_plan.backends]
            new_backends = select_best_backends(run_plan)
            if not new_backends:
                log.error(_(u"Can't update '{name}', no backend "
                            u"available").format(name=self.name))
                return

            kwargs = {}
            if len(current_backends) > 1 or len(new_backends) > 1:
                vtask = VirtualTask(
                    title=_(u"Updating application {name}").format(
                        name=self.name))
                vtask.save()
                kwargs['parent'] = vtask

            for backend_conf in new_backends:
                if backend_conf.backend in current_backends:
                    Task.put('UpdateVassalTask', backend=backend_conf.backend,
                             application=self, package=self.current_package,
                             **kwargs)
                else:
                    # add backend to run plan if not already there
                    ApplicationRunPlan.objects(
                        id=self.run_plan.id,
                        backends__backend__nin=[
                            backend_conf.backend]).update_one(
                        push__backends=backend_conf.backend)
                    Task.put('StartPackageTask', backend=backend_conf.backend,
                             application=self, package=self.current_package,
                             **kwargs)

            for backend in current_backends:
                if backend not in new_backends:
                    log.info(_(u"Stopping {name} on old backend "
                               u"{backend}").format(name=self.name,
                                                    backend=backend.name))
                    Task.put('StopPackageTask', backend=backend,
                             application=self, package=self.current_package,
                             **kwargs)

    def trim_package_files(self):
        """
        Removes over limit package files from database. Number of packages per
        app that are kept in database for rollback feature are set in user
        limits as 'packages_per_app'.
        """
        storage = find_storage_handler(self.upaas_config)
        if not storage:
            log.error(u"Storage handler '%s' not found, cannot trim "
                      u"packages" % self.upaas_config.storage.handler)
            return

        removed = 0
        for pkg in Package.objects(application=self, filename__exists=True)[
                self.owner.limits['packages_per_app']:]:
            if pkg.id == self.current_package.id:
                continue
            removed += 1
            if storage.exists(pkg.filename):
                log.info(u"Removing package %s file from "
                         u"database" % pkg.safe_id)
                storage.delete(pkg.filename)
            del pkg.filename
            pkg.save()

        if removed:
            log.info(u"Removed %d package file(s) for app %s" % (removed,
                                                                 self.name))

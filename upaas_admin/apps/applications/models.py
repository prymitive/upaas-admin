# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

from __future__ import unicode_literals

import os
import datetime
import logging
import tempfile
import shutil
import time
import re
from copy import deepcopy

from mongoengine import (Document, DateTimeField, StringField, LongField,
                         ReferenceField, ListField, DictField, QuerySetManager,
                         BooleanField, IntField, NULLIFY, signals)

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

from upaas_admin.apps.servers.models import RouterServer, BackendServer
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.scheduler.base import select_best_backends
from upaas_admin.apps.tasks.constants import TaskStatus
from upaas_admin.apps.tasks.models import Task
from upaas_admin.apps.applications.constants import (
    NeedsBuildingFlag, NeedsStoppingFlag, NeedsRestartFlag, NeedsRemovingFlag,
    IsStartingFlag, FLAGS_BY_NAME)


log = logging.getLogger(__name__)


class Package(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    metadata = StringField(help_text=_('Application metadata'))
    application = ReferenceField('Application', dbref=False, required=True)

    interpreter_name = StringField(required=True)
    interpreter_version = StringField(required=True)

    parent = StringField()
    parent_package = ReferenceField('Package')
    filename = StringField()
    bytes = LongField(required=True)
    checksum = StringField(required=True)
    builder = StringField(required=True)

    distro_name = StringField(required=True)
    distro_version = StringField(required=True)
    distro_arch = StringField(required=True)

    revision_id = StringField()
    revision_author = StringField()
    revision_date = DateTimeField()
    revision_description = StringField()
    revision_changelog = StringField()

    ack_filename = '.upaas-unpacked'

    meta = {
        'indexes': ['filename'],
        'ordering': ['-date_created'],
    }

    _default_manager = QuerySetManager()

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        log.debug(_("Pre delete signal on package {id}").format(
            id=document.safe_id))
        Application.objects(id=document.application.id).update_one(
            pull__packages=document.id)
        document.delete_package_file(null_filename=False)

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

    @property
    def ack_path(self):
        return os.path.join(self.package_path, self.ack_filename)

    def delete_package_file(self, null_filename=True):
        log.debug(_("Deleting package file for {pkg}").format(
            pkg=self.safe_id))
        if not self.filename:
            log.debug(_("Package {pkg} has no filename, skipping "
                        "delete").format(pkg=self.safe_id))
            return

        storage = find_storage_handler(self.upaas_config.storage.handler,
                                       self.upaas_config.storage.settings)
        if not storage:
            log.error(_("Storage handler '{handler}' not found, cannot "
                        "package file").format(
                handler=self.upaas_config.storage.handler))
            return

        log.debug(_("Checking if package file {path} is stored").format(
            path=self.filename))
        if storage.exists(self.filename):
            log.info(_("Removing package {pkg} file from storage").format(
                pkg=self.safe_id))
            storage.delete(self.filename)
        if null_filename:
            log.info(_("Clearing filename for package {pkg}").format(
                pkg=self.safe_id))
            del self.filename
            self.save()

    def uwsgi_options_from_metadata(self):
        """
        Parse uWSGI options in metadata (if any) and return only allowed.
        """
        options = []
        compiled = []

        for regexp in self.upaas_config.apps.uwsgi.safe_options:
            compiled.append(re.compile(regexp))

        for opt in self.metadata_config.uwsgi.settings:
            if '=' in opt:
                for regexp in compiled:
                    opt_name = opt.split('=')[0].rstrip(' ')
                    if regexp.match(opt_name):
                        options.append(opt)
                        log.debug(_("Adding safe uWSGI option from metadata: "
                                    "{opt}").format(opt=opt))
                        break

        return options

    def generate_uwsgi_config(self, backend_conf):
        """
        :param backend_conf: BackendRunPlanSettings instance for which we
                             generate config
        """

        def _load_template(path):
            log.debug("Loading uWSGI template from: %s" % path)
            for search_path in UPAAS_CONFIG_DIRS:
                template_path = os.path.join(search_path, path)
                if os.path.exists(template_path):
                    f = open(template_path)
                    ret = f.read().splitlines()
                    f.close()
                    return ret
            return []

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

        run_plan = self.application.run_plan

        max_memory = backend_conf.workers_max
        max_memory *= run_plan.memory_per_worker
        max_memory *= 1024 * 1024

        variables = {
            'namespace': self.package_path,
            'chdir': config.apps.home,
            'socket': '%s:%d' % (backend_conf.backend.ip, backend_conf.socket),
            'stats': '%s:%d' % (backend_conf.backend.ip, backend_conf.stats),
            'uid': config.apps.uid,
            'gid': config.apps.gid,
            'app_name': self.application.name,
            'app_id': self.application.safe_id,
            'pkg_id': self.safe_id,
            'max_workers': backend_conf.workers_max,
            'max_memory': max_memory,
            'memory_per_worker': run_plan.memory_per_worker,
            'max_log_size': run_plan.max_log_size * 1024 * 1024,
        }

        if config.apps.graphite.carbon:
            variables['carbon_servers'] = ' '.join(
                config.apps.graphite.carbon)
            variables['carbon_timeout'] = config.apps.graphite.timeout
            variables['carbon_frequency'] = config.apps.graphite.frequency
            variables['carbon_max_retry'] = config.apps.graphite.max_retry
            variables['carbon_retry_delay'] = config.apps.graphite.retry_delay
            variables['carbon_root'] = config.apps.graphite.root

        try:
            variables.update(config.interpreters[self.interpreter_name]['any'][
                'uwsgi']['vars'])
        except (AttributeError, KeyError):
            pass
        try:
            variables.update(config.interpreters[self.interpreter_name][
                self.interpreter_version]['uwsgi']['vars'])
        except (AttributeError, KeyError):
            pass

        # interpretere default settings for any version
        try:
            for key, value in list(config.interpreters[self.interpreter_name][
                    'any']['settings'].items()):
                var_name = "meta_%s_%s" % (self.interpreter_name, key)
                variables[var_name] = value
        except (AttributeError, KeyError):
            pass
        # interpretere default settings for current version
        try:
            for key, value in list(config.interpreters[self.interpreter_name][
                    self.interpreter_version]['settings'].items()):
                var_name = "meta_%s_%s" % (self.interpreter_name, key)
                variables[var_name] = value
        except (AttributeError, KeyError):
            pass
        # interpreter settings from metadata
        try:
            for key, val in list(
                    self.metadata_config.interpreter.settings.items()):
                var_name = "meta_%s_%s" % (self.interpreter_name, key)
                variables[var_name] = val
        except KeyError:
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
        envs.update(self.metadata_config.env)

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
        for key, value in list(variables.items()):
            options.append('var_%s = %s' % (key, value))

        options.append('\n# starting ENV variables list')
        for key, value in list(envs.items()):
            options.append('env = %s=%s' % (key, value))
        options.append(
            'env = UPAAS_SYSTEM_DOMAIN=%s' % self.application.system_domain)
        if self.application.custom_domains:
            options.append('env = UPAAS_CUSTOM_DOMAINS=%s' % ','.join(
                [d.name for d in self.application.custom_domains]))

        options.append('\n# starting options from app metadata')
        for opt in self.uwsgi_options_from_metadata():
            options.append(opt)

        # enable cheaper mode if we have multiple workers
        if backend_conf.workers_max > backend_conf.workers_min:
            options.append('\n# enabling cheaper mode')
            options.append('cheaper = %d' % backend_conf.workers_min)

        options.append('\n# starting base template')
        options.extend(_load_template(base_template))

        if config.apps.graphite.carbon:
            options.append('\n# starting carbon servers block')
            for carbon in config.apps.graphite.carbon:
                options.append('carbon = %s' % carbon)

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
            for domain in self.application.custom_domains:
                options.append('subscribe2 = server=%s:%d,key=%s' % (
                    router.private_ip, router.subscription_port, domain.name))

        options.append('\n')
        return options

    def check_vassal_config(self, options):
        """
        Verify is there is uWSGI vassal configuration file and if it doesn't
         need updating.
        """
        if os.path.exists(self.application.vassal_path):
            current_hash = calculate_file_sha256(self.application.vassal_path)
            new_hash = calculate_string_sha256(options)
            if current_hash == new_hash:
                return True
        return False

    def save_vassal_config(self, backend):
        log.info("Generating uWSGI vassal configuration")
        options = "\n".join(self.generate_uwsgi_config(backend))

        if self.check_vassal_config(options):
            log.info("Vassal is present and valid, skipping rewrite")
            return

        log.info("Saving vassal configuration to "
                 "'%s'" % self.application.vassal_path)
        with open(self.application.vassal_path, 'w') as vassal:
            vassal.write(options)
        log.info("Vassal saved")

    def unpack(self):
        # directory is encoded into string to prevent unicode errors
        directory = tempfile.mkdtemp(dir=self.upaas_config.paths.workdir,
                                     prefix="upaas_package_").encode("utf-8")

        storage = find_storage_handler(self.upaas_config.storage.handler,
                                       self.upaas_config.storage.settings)
        if not storage:
            log.error("Storage handler '%s' not "
                      "found" % self.upaas_config.storage.handler)

        workdir = os.path.join(directory, "system")
        pkg_path = os.path.join(directory, self.filename)

        if os.path.exists(self.package_path):
            log.error("Package directory already exists: "
                      "%s" % self.package_path)
            raise UnpackError("Package directory already exists")

        log.info("Fetching package '%s'" % self.filename)
        try:
            storage.get(self.filename, pkg_path)
        except StorageError:
            log.error("Storage error while fetching package "
                      "'%s'" % self.filename)
            utils.rmdirs(directory)
            raise StorageError("Can't fetch package '%s' from "
                               "storage" % self.filename)

        log.info("Unpacking package")
        os.mkdir(workdir, 0o755)
        if not tar.unpack_tar(pkg_path, workdir):
            log.error("Error while unpacking package to '%s'" % workdir)
            utils.rmdirs(directory)
            raise UnpackError("Error during package unpack")

        with open(os.path.join(workdir, self.ack_filename), 'w') as ack:
            ack.write(_('Unpacked: {now}').format(now=datetime.datetime.now()))

        log.info("Package unpacked, moving into '%s'" % self.package_path)
        try:
            shutil.move(workdir, self.package_path)
        except shutil.Error as e:
            log.error("Error while moving unpacked package to final "
                      "destination: %s" % e)
            utils.rmdirs(directory, self.package_path)
            raise UnpackError("Can't move to final directory "
                              "'%s'" % self.package_path)
        log.info("Package moved")
        utils.rmdirs(directory)


class ApplicationDomain(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    application = ReferenceField('Application', dbref=False, required=True)
    name = StringField(required=True, unique=True, min_length=4, max_length=64)
    validated = BooleanField()

    @property
    def safe_id(self):
        return str(self.id)


class FlagLock(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    application = ReferenceField('Application', dbref=False, required=True)
    flag = StringField(required=True)
    backend = ReferenceField(BackendServer, reverse_delete_rule=NULLIFY)
    pid = IntField(required=True)

    meta = {
        'indexes': [
            {'fields': ['application', 'flag', 'backend'], 'unique': True},
        ],
        'ordering': ['-date_created'],
    }


class ApplicationFlag(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    application = ReferenceField('Application', dbref=False, required=True)
    name = StringField(required=True, unique_with='application')
    options = DictField()
    pending = BooleanField(default=True)
    pending_backends = ListField(ReferenceField(BackendServer))

    meta = {
        'indexes': [
            {'fields': ['name', 'application'], 'unique': True},
            # TODO add indexes after profiling
        ],
        'ordering': ['-date_created'],
    }

    @property
    def title(self):
        return FLAGS_BY_NAME.get(self.name).title


class Application(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, min_length=2, max_length=60,
                       unique_with='owner', verbose_name=_('name'))
    # FIXME reverse_delete_rule=DENY for owner
    owner = ReferenceField('User', dbref=False, required=True)
    metadata = StringField(verbose_name=_('Application metadata'),
                           required=True)
    current_package = ReferenceField(Package, dbref=False, required=False)
    packages = ListField(ReferenceField(Package, dbref=False,
                                        reverse_delete_rule=NULLIFY))

    _default_manager = QuerySetManager()

    meta = {
        'indexes': [
            {'fields': ['name', 'owner'], 'unique': True},
            {'fields': ['packages']},
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
    def supported_interpreter_versions(self):
        """
        Return list of interpreter versions that this app can run.
        """
        if self.metadata:
            return sorted(list(utils.supported_versions(
                self.upaas_config, self.metadata_config).keys()), reverse=True)

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
        return Task.objects(application=self)

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
        return self.tasks.filter(flag=NeedsBuildingFlag.name)

    @property
    def running_build_tasks(self):
        """
        Returns list of running build tasks for this application.
        """
        return self.build_tasks.filter(status=TaskStatus.running)

    @property
    def flags(self):
        """
        Return list of application flags.
        """
        return ApplicationFlag.objects(application=self)

    @property
    def system_domain(self):
        """
        Returns automatic system domain for this application.
        """
        return '%s.%s' % (self.safe_id, self.upaas_config.apps.domains.system)

    @property
    def custom_domains(self):
        """
        List of custom domains assigned for this application.
        """
        return ApplicationDomain.objects(application=self)

    @property
    def domain_validation_code(self):
        """
        String used for domain ownership validation.
        """
        return "upaas-app-id=%s" % self.safe_id

    @property
    def router_ip_list(self):
        return [r.public_ip for r in RouterServer.objects(is_enabled=True)]

    def get_absolute_url(self):
        return reverse('app_details', args=[self.safe_id])

    def build_package(self, force_fresh=False, interpreter_version=None):
        q = {
            'set__options__{0:s}'.format(
                NeedsBuildingFlag.Options.build_fresh_package): force_fresh,
            'set__options__{0:s}'.format(
                NeedsBuildingFlag.Options.build_interpreter_version):
                    interpreter_version,
            'unset__pending': True,
            'upsert': True
        }
        ApplicationFlag.objects(application=self,
                                name=NeedsBuildingFlag.name).update_one(**q)

    def start_application(self):
        if self.current_package:
            run_plan = self.run_plan
            if not run_plan:
                log.error("Trying to start '%s' without run plan" % self.name)
                return

            backends = select_best_backends(run_plan,
                                            package=self.current_package)
            if not backends:
                log.error(_("Can't start '{name}', no backend "
                            "available").format(name=self.name))
                run_plan.delete()
                return

            run_plan.backends = backends
            run_plan.save()
            ApplicationFlag.objects(
                application=self, name=IsStartingFlag.name).update_one(
                    set__pending_backends=[b.backend for b in backends],
                    upsert=True)
            ApplicationFlag.objects(name=NeedsStoppingFlag.name,
                                    application=self).delete()

    def stop_application(self):
        if self.current_package:
            if not self.run_plan:
                return
            if self.run_plan and not self.run_plan.backends:
                # no backends in run plan, just delete it
                self.run_plan.delete()
                return
        ApplicationFlag.objects(
            application=self, name=NeedsStoppingFlag.name).update_one(
                set__pending_backends=[
                    b.backend for b in self.run_plan.backends], upsert=True)
        ApplicationFlag.objects(name=IsStartingFlag.name,
                                application=self).delete()

    def restart_application(self):
        if self.current_package:
            if not self.run_plan:
                return
        ApplicationFlag.objects(
            application=self, name=NeedsRestartFlag.name).update_one(
                set__pending_backends=[
                    b.backend for b in self.run_plan.backends], upsert=True)

    def update_application(self):
        if self.run_plan:

            run_plan = self.run_plan

            current_backends = [bc.backend for bc in run_plan.backends]
            new_backends = select_best_backends(run_plan)
            if not new_backends:
                log.error(_("Can't update '{name}', no backend "
                            "available").format(name=self.name))
                return

            updated_backends = []
            for backend_conf in new_backends:
                if backend_conf.backend in current_backends:
                    # replace backend settings with updated version
                    run_plan.update(
                        pull__backends__backend=backend_conf.backend)
                    run_plan.update(push__backends=backend_conf)
                    updated_backends.append(backend_conf.backend)
                else:
                    # add backend to run plan if not already there
                    ApplicationRunPlan.objects(
                        id=self.run_plan.id,
                        backends__backend__nin=[
                            backend_conf.backend]).update_one(
                        push__backends=backend_conf)
                    log.info(_("Starting {name} on backend {backend}").format(
                        name=self.name, backend=backend_conf.backend.name))
                    ApplicationFlag.objects(
                        pending_backends__ne=backend_conf.backend,
                        application=self,
                        name=IsStartingFlag.name).update_one(
                            add_to_set__pending_backends=backend_conf.backend,
                            upsert=True)

            if updated_backends:
                ApplicationFlag.objects(
                    application=self, name=NeedsRestartFlag.name).update_one(
                        set__pending_backends=updated_backends, upsert=True)

            for backend in current_backends:
                if backend not in [bc.backend for bc in new_backends]:
                    log.info(_("Stopping {name} on old backend "
                               "{backend}").format(name=self.name,
                                                   backend=backend.name))
                    ApplicationFlag.objects(
                        pending_backends__ne=backend,
                        application=self,
                        name=NeedsRemovingFlag.name).update_one(
                            add_to_set__pending_backends=backend, upsert=True)

    def trim_package_files(self):
        """
        Removes over limit package files from database. Number of packages per
        app that are kept in database for rollback feature are set in user
        limits as 'packages_per_app'.
        """
        storage = find_storage_handler(self.upaas_config.storage.handler,
                                       self.upaas_config.storage.settings)
        if not storage:
            log.error("Storage handler '%s' not found, cannot trim "
                      "packages" % self.upaas_config.storage.handler)
            return

        removed = 0
        for pkg in Package.objects(application=self, filename__exists=True)[
                self.owner.limits['packages_per_app']:]:
            if pkg.id == self.current_package.id:
                continue
            removed += 1
            pkg.delete_package_file(null_filename=True)

        if removed:
            log.info("Removed %d package file(s) for app %s" % (removed,
                                                                self.name))

    def remove_unpacked_packages(self, exclude=None, timeout=None):
        """
        Remove all but current unpacked packages
        """
        if timeout is None:
            timeout = self.upaas_config.commands.timelimit
        log.info(_("Cleaning packages for {name}").format(name=self.name))
        for pkg in self.packages:
            if exclude and pkg.id in exclude:
                # skip current package!
                continue
            if os.path.isdir(pkg.package_path):
                log.info(_("Removing package directory {path}").format(
                    path=pkg.package_path))

                # if there are running pids inside package dir we will need to
                # wait this should only happen during upgrade, when we need to
                # wait for app to reload into new package dir
                started_at = datetime.datetime.now()
                timeout_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=timeout)
                pids = processes.directory_pids(pkg.package_path)
                while pids:
                    if datetime.datetime.now() > timeout_at:
                        log.error(_("Timeout reached while waiting for pids "
                                    "in {path} to die, killing any remaining "
                                    "processes").format(
                            path=pkg.package_path))
                        break
                    log.info(_("Waiting for {pids} pid(s) in {path} to "
                               "terminate").format(pids=len(pids),
                                                   path=pkg.package_path))
                    time.sleep(2)
                    pids = processes.directory_pids(pkg.package_path)

                try:
                    processes.kill_and_remove_dir(pkg.package_path)
                except OSError as e:
                    log.error(_("Exception during package directory cleanup: "
                                "{e}").format(e=e))


signals.pre_delete.connect(Package.pre_delete, sender=Package)

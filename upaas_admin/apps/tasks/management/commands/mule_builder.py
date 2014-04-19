# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging
from os import getpid
from signal import signal, SIGINT, SIGTERM
from datetime import datetime
from time import sleep
from socket import gethostname

from IPy import IP

from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext as _

from upaas.builder.builder import Builder
from upaas.builder.exceptions import BuildError
from upaas.inet import local_ipv4_addresses
from upaas.processes import is_pid_running

from upaas_admin.config import load_main_config
from upaas_admin.apps.applications.constants import Flags
from upaas_admin.apps.applications.models import ApplicationFlag, Package
from upaas_admin.apps.servers.models import BackendServer
from upaas_admin.apps.tasks.models import MongoLogHandler, TaskDetails
from upaas_admin.apps.tasks.constants import TaskStatus


log = logging.getLogger(__name__)


class Command(NoArgsCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.is_exiting = False
        self.cleanup()
        self.pid = getpid()
        self.register_backend()
        self.log_handler = None
        self.log_handlers_level = {}
        # FIXME capture all logs and prefix with self.logger

    def add_logger(self, task):
        self.log_handler = MongoLogHandler(task)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            self.log_handlers_level[handler] = handler.level
            handler.level = logging.ERROR
        root_logger.addHandler(self.log_handler)

    def remove_logger(self):
        self.log_handler.flush()
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            level = self.log_handlers_level.get(handler)
            if level is not None:
                handler.level = level
        root_logger.removeHandler(self.log_handler)

    def mark_exiting(self, *args):
        log.info(_("Exiting, waiting for current task to finish"))
        self.is_exiting = True

    def fail(self, flag, task):
        flag.delete()
        self.remove_logger()
        self.cleanup()
        task.update(set__status=TaskStatus.failed)
        log.error(_("Building completed for {name} [{id}]").format(
            name=task.application.name, id=task.application.safe_id))

    def cleanup(self):
        self.app_name = _('N/A')

    def handle_noargs(self, **options):
        signal(SIGINT, self.mark_exiting)
        signal(SIGTERM, self.mark_exiting)

        while True:
            if self.is_exiting:
                return

            flag = self.find_flag()
            if flag:
                if flag.locked_since:
                    if flag.locked_by_pid != self.pid:
                        if not is_pid_running(flag.locked_by_pid):
                            log.warning(_("Found flag locked by non-existing "
                                          "PID {pid}").format(
                                pid=flag.locked_by_pid))
                            self.unlock_flag(flag)
                            continue

                app = flag.application
                self.app_name = app.name
                current_package = app.current_package
                force_fresh = flag.options.get(Flags.build_fresh_package,
                                               False)
                interpreter_version = flag.options.get(
                    Flags.build_interpreter_version)

                system_filename = None
                current_revision = None
                if not force_fresh and current_package:
                    system_filename = current_package.filename
                    current_revision = current_package.revision_id
                    interpreter_version = current_package.interpreter_version

                log.info(_("Building new package for {name} [{id}]").format(
                    name=app.name, id=app.safe_id))

                task = TaskDetails(backend=self.backend, pid=self.pid,
                                   flag=flag.name, application=app)
                task.save()
                self.add_logger(task)

                metadata = flag.application.metadata
                metadata_obj = flag.application.metadata_config
                if not metadata or not metadata_obj:
                    log.error(_("Missing or invalid application metadata"))
                    self.fail(flag, task)
                    continue

                upaas_config = load_main_config()
                if not upaas_config:
                    log.error(_("Missing or invalid uPaaS configuration"))
                    self.fail(flag, task)
                    continue

                log.info(_("Building package for application {name} "
                           "[{id}]").format(name=flag.application.name,
                                            id=flag.application.safe_id))
                log.info(_("Fresh package: {fresh}").format(fresh=force_fresh))
                log.info(_("Base image: {name}").format(name=system_filename))
                log.info(_("Interpreter version: {ver}").format(
                    ver=interpreter_version))
                log.info(_("Current revision: {rev}").format(
                    rev=current_revision))

                build_result = None
                try:
                    builder = Builder(upaas_config, metadata_obj)
                    for result in builder.build_package(
                            system_filename=system_filename,
                            interpreter_version=interpreter_version,
                            current_revision=current_revision):
                        log.debug(_("Build progress: {proc}%").format(
                            proc=result.progress))
                        build_result = result
                        task.update(set__progress=result.progress)
                except BuildError:
                    self.fail(flag, task)
                    continue
                else:
                    self.create_package(app, metadata_obj, metadata,
                                        build_result, current_package)

                flag.reload()
                if not flag.pending:
                    flag.delete()
                task.update(set__status=TaskStatus.successful)
                self.remove_logger()
                self.cleanup()

                log.info(_("Building completed for {name} [{id}]").format(
                    name=app.name, id=app.safe_id))
            else:
                sleep(2)

    def create_package(self, app, metadata_obj, metadata, build_result,
                       parent_package):
        log.info("Building completed")
        pkg = Package(metadata=metadata,
                      application=app,
                      interpreter_name=metadata_obj.interpreter.type,
                      interpreter_version=build_result.interpreter_version,
                      bytes=build_result.bytes,
                      filename=build_result.filename,
                      checksum=build_result.checksum,
                      parent=build_result.parent,
                      builder=self.backend.name,
                      distro_name=build_result.distro_name,
                      distro_version=build_result.distro_version,
                      distro_arch=build_result.distro_arch)
        if parent_package and build_result.parent == parent_package.filename:
            pkg.parent_package = parent_package
        if build_result.vcs_revision.get('id'):
            pkg.revision_id = build_result.vcs_revision.get('id')
        if build_result.vcs_revision.get('author'):
            pkg.revision_author = build_result.vcs_revision.get('author')
        if build_result.vcs_revision.get('date'):
            pkg.revision_date = build_result.vcs_revision.get('date')
        if build_result.vcs_revision.get('description'):
            pkg.revision_description = build_result.vcs_revision.get(
                'description')
        if build_result.vcs_revision.get('changelog'):
            pkg.revision_changelog = build_result.vcs_revision.get(
                'changelog')
        pkg.save()
        log.info(_("Package created with id {id}").format(id=pkg.safe_id))

        app.reload()
        app.packages.append(pkg)
        app.current_package = pkg
        app.save()
        log.info(_("Application updated"))
        app.upgrade_application()
        app.trim_package_files()

    def find_flag(self):
        """
        Find application that needs new package, return None if nothing to do.
        """
        ApplicationFlag.objects(
            pending__ne=False,
            name=Flags.needs_building).update_one(
                set__pending=False,
                set__locked_since=datetime.now(),
                set__locked_by_backend=self.backend,
                set__locked_by_pid=self.pid)
        return ApplicationFlag.objects(name=Flags.needs_building,
                                       locked_by_backend=self.backend,
                                       pending=False).first()

    def unlock_flag(self, flag):
        flag.update(set__pending=True,
                    unset__locked_since=True,
                    unset__locked_by_backend=True,
                    unset__locked_by_pid=True)

    def register_backend(self):
        name = gethostname()
        local_ip = None

        backend = BackendServer.objects(name=name).first()
        if not backend:
            for local_ip in local_ipv4_addresses():
                backend = BackendServer.objects(ip=local_ip).first()
                if backend:
                    break

        if not backend and not local_ip:
            log.error("No IP address found for local backend!")
            return

        if backend:
            local_ips = local_ipv4_addresses()
            if backend.ip not in [IP(ip) for ip in local_ips]:
                local_ip = local_ips[0]
                log.info("Updating IP for '%s' from '%s' to '%s'" % (
                    name, backend.ip, local_ip))
                backend.ip = IP(local_ip)
                backend.save()
        else:
            log.info(_("Local backend not found, registering as '{name}' "
                       "with IP {ip}").format(name=name, ip=local_ip))
            backend = BackendServer(name=name, ip=local_ip, is_enabled=False)
            backend.save()

        self.backend = backend

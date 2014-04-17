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
from django.utils.translation import ugettext_lazy as _

from upaas.builder.builder import Builder
from upaas.builder.exceptions import BuildError
from upaas.inet import local_ipv4_addresses
from upaas.processes import is_pid_running

from upaas_admin.config import load_main_config
from upaas_admin.apps.applications.constants import Flags
from upaas_admin.apps.applications.models import ApplicationFlag, Package
from upaas_admin.apps.servers.models import BackendServer


log = logging.getLogger(__name__)


class Command(NoArgsCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.is_exiting = False
        self.cleanup()
        self.pid = getpid()
        self.register_backend()
        # FIXME capture all logs and prefix with self.logger
        # TODO add task object with messages and progress

    def logger(self, msg, level=logging.INFO):
        log.log(level, _("[Building: {name}] [PID: {pid}] {msg}").format(
            name=self.app_name, pid=self.pid, msg=msg))

    def mark_exiting(self, *args):
        self.logger(_("Exiting, waiting for current task to finish"))
        self.is_exiting = True

    def fail(self, flag):
        self.logger(_("Build failed"), level=logging.ERROR)
        flag.delete()
        self.cleanup()

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
                            self.logger(_("Found flag locked by non-existing "
                                          "PID ({pid})").format(
                                              pid=flag.locked_by_pid),
                                        level=logging.WARNING)
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

                metadata = flag.application.metadata
                metadata_obj = flag.application.metadata_config
                if not metadata or not metadata_obj:
                    self.logger(_("Missing or invalid application metadata"),
                                level=logging.ERROR)
                    self.fail(flag)
                    continue

                upaas_config = load_main_config()
                if not upaas_config:
                    self.logger(_("Missing or invalid uPaaS configuration"),
                                level=logging.ERROR)
                    self.fail(flag)
                    continue

                self.logger(_("Building package for application {name} "
                              "[{id}]").format(name=flag.application.name,
                                               id=flag.application.safe_id))
                self.logger(_("Fresh package: {fresh}").format(
                    fresh=force_fresh))
                self.logger(_("Base image: {name}").format(
                    name=system_filename))
                self.logger(_("Interpreter version: {ver}").format(
                    ver=interpreter_version))
                self.logger(_("Current revision: {rev}").format(
                    rev=current_revision))

                build_result = None
                try:
                    builder = Builder(upaas_config, metadata_obj)
                    for result in builder.build_package(
                            system_filename=system_filename,
                            interpreter_version=interpreter_version,
                            current_revision=current_revision):
                        self.logger(_("Build progress: {proc}%%").format(
                            proc=result.progress))
                        build_result = result
                except BuildError:
                    self.logger(_("Build failed"))
                    self.cleanup(flag)
                else:
                    self.create_package(app, metadata_obj, metadata,
                                        build_result, current_package)

                flag.reload()
                if not flag.pending:
                    flag.delete()
                self.cleanup()
            else:
                sleep(2)

    def create_package(self, app, metadata_obj, metadata, build_result,
                       parent_package):
        self.logger("Building completed")
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
        self.logger(_("Package created with id {id}").format(id=pkg.safe_id))

        app.reload()
        app.packages.append(pkg)
        app.current_package = pkg
        app.save()
        self.logger(_("Application updated"))
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
            self.logger("No IP address found for local backend!",
                        level=logging.ERROR)
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
            self.logger(_("Local backend not found, registering as '{name}' "
                          "with IP {ip}").format(name=name, ip=local_ip))
            backend = BackendServer(name=name, ip=local_ip, is_enabled=False)
            backend.save()

        self.backend = backend

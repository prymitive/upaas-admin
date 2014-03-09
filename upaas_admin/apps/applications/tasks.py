# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import logging
from socket import gethostname

from mongoengine import StringField, ReferenceField, BooleanField

from django.utils.translation import ugettext_lazy as _

from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError

from upaas_admin.config import load_main_config
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.applications.models import Package
from upaas_admin.apps.tasks.base import (ApplicationTask,
                                         ApplicationBackendTask)
from upaas_admin.apps.tasks.registry import register


log = logging.getLogger(__name__)


#TODO translations

@register
class BuildPackageTask(ApplicationTask):

    application = ReferenceField('Application', dbref=False, required=True)
    metadata = StringField(required=True)
    force_fresh = BooleanField(default=False)
    interpreter_version = StringField()

    def generate_title(self):
        if self.force_fresh:
            return _("Building new fresh package for {name}").format(
                name=self.application.name)
        else:
            return _("Building new package for {name}").format(
                name=self.application.name)

    def job(self):

        try:
            metadata_obj = MetadataConfig.from_string(self.metadata)
        except ConfigurationError:
            log.error("Invalid app metadata")
            raise Exception()

        upaas_config = load_main_config()
        if not upaas_config:
            log.error("Missing uPaaS configuration")
            raise Exception()

        system_filename = None
        parent_package = None
        current_revision = None
        if not self.force_fresh and self.application.current_package:
            system_filename = self.application.current_package.filename
            parent_package = self.application.current_package
            current_revision = self.application.current_package.revision_id
            self.interpreter_version = \
                self.application.current_package.interpreter_version
            log.info(_("Using current application package {pkg} as "
                       "parent").format(pkg=parent_package.safe_id))

        log.info("Starting build task with parameters app_id=%s, "
                 "force_fresh=%s, interpreter_version=%s, "
                 "current_revision=%s" % (
                     self.application.safe_id, self.force_fresh,
                     self.interpreter_version, current_revision))

        build_result = None
        try:
            builder = Builder(upaas_config, metadata_obj)
            for result in builder.build_package(
                    system_filename=system_filename,
                    interpreter_version=self.interpreter_version,
                    current_revision=current_revision):
                log.debug("Build progress: %d%%" % result.progress)
                yield result.progress
                build_result = result
        except exceptions.BuildError:
            log.error("Build failed")
            raise Exception()

        log.info("Build completed")
        pkg = Package(metadata=self.metadata,
                      application=self.application,
                      interpreter_name=metadata_obj.interpreter.type,
                      interpreter_version=build_result.interpreter_version,
                      bytes=build_result.bytes,
                      filename=build_result.filename,
                      checksum=build_result.checksum,
                      parent=build_result.parent,
                      builder=gethostname(),
                      distro_name=build_result.distro_name,
                      distro_version=build_result.distro_version,
                      distro_arch=build_result.distro_arch,
                      revision_id=build_result.vcs_revision.get('id'),
                      revision_author=build_result.vcs_revision.get('author'),
                      revision_date=build_result.vcs_revision.get('date'),
                      revision_description=build_result.vcs_revision.get(
                          'description'),
                      revision_changelog=build_result.vcs_revision.get(
                          'changelog'),
                      )
        if parent_package and build_result.parent == parent_package.filename:
            pkg.parent_package = parent_package
        pkg.save()
        log.info("Package saved with id %s" % pkg.id)

        self.application.reload()
        self.application.packages.append(pkg)
        self.application.current_package = pkg
        self.application.save()
        log.info("Application '%s' updated" % self.application.name)
        self.application.upgrade_application()
        self.application.trim_package_files()


@register
class StartApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Starting {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):

        if not self.application.run_plan:
            log.error("Missing run plan, cannot start "
                      "'%s'" % self.application.name)
            raise Exception("Missing run plan for "
                            "'%s'" % self.application.name)

        run_plan = self.application.run_plan

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            if backend_conf.package.id != self.application.current_package.id:
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
            log.info("Starting application '%s' using package '%s'" % (
                self.application.name, backend_conf.package.safe_id))

            if not os.path.exists(backend_conf.package.package_path):
                try:
                    backend_conf.package.unpack()
                except UnpackError as e:
                    log.error("Unpacking failed: %s" % e)
                    raise Exception("Unpacking package failed: %s" % e)
            else:
                log.warning("Package already exists: "
                            "%s" % backend_conf.package.package_path)
            yield 50

            backend_conf.package.save_vassal_config(backend_conf)
            # TODO handle backend start task failure with rescue code

            self.wait_until_running()
            yield 100
        else:
            log.error(_("Backend {backend} missing in run plan for "
                        "{name}").format(backend=self.backend.name,
                                         name=self.application.name))
            yield 100


@register
class StopApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Stopping {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        if os.path.isfile(self.application.vassal_path):
            log.info("Removing vassal config file "
                     "'%s'" % self.application.vassal_path)
            try:
                os.remove(self.application.vassal_path)
            except OSError as e:
                log.error("Can't remove vassal config file at '%s': %s" % (
                    self.application.vassal_path, e))
                raise
        else:
            log.warning("Vassal config file for application '%s' not found "
                        "at '%s" % (self.application.safe_id,
                                    self.application.vassal_path))
        yield 10

        self.wait_until_stopped()
        yield 75

        run_plan = self.application.run_plan
        if run_plan:
            run_plan.remove_backend_settings(self.backend)
        else:
            log.warning(_("Missing run plan for {name}, already "
                          "stopped?").format(name=self.application.name))

        self.application.remove_unpacked_packages()
        log.info("Application '%s' stopped" % self.application.name)
        yield 100

    def cleanup(self):
        run_plan = self.application.run_plan
        if run_plan and not run_plan.backends:
            log.info("Removing '%s' run plan" % self.application.name)
            run_plan.delete()


@register
class UpgradeApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Upgrading {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        run_plan = self.application.run_plan
        if not run_plan:
            msg = str(_("Missing run plan for {name}, cannot "
                        "upgrade").format(name=self.application.name))
            log.warning(msg)
            raise Exception(msg)

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            if backend_conf.package.id != self.application.current_package.id:
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
            try:
                backend_conf.package.unpack()
            except UnpackError:
                log.error("Unpacking failed")
                raise
            yield 40

            backend_conf.package.save_vassal_config(backend_conf)
            yield 75

            self.wait_until_running()
            yield 95

            self.application.remove_unpacked_packages(
                exclude=[backend_conf.package.id])
            yield 100
        else:
            log.warning(_("No run plan for {name}, it was probably "
                          "stopped").format(name=self.application.name))
            yield 100


@register
class UpdateVassalTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Updating {name} configuration on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        run_plan = self.application.run_plan
        if not run_plan:
            msg = str(_("Missing run plan for {name}, application was "
                        "already stopped?").format(
                name=self.application.name))
            log.warning(msg)
            yield 100
            raise StopIteration

        backend_conf = self.application.run_plan.backend_settings(self.backend)
        if backend_conf:

            if backend_conf.package.id != self.application.current_package.id:
                log.info(_("Old package on backend, running upgrade"))
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
                try:
                    backend_conf.package.unpack()
                except UnpackError:
                    log.error("Unpacking failed")
                    raise
                yield 40

            backend_conf.package.save_vassal_config(backend_conf)
            yield 50

            self.wait_until_running()
            yield 95

            self.application.remove_unpacked_packages(
                exclude=[backend_conf.package.id])
            yield 100
        else:
            log.warning(_("No run plan for {name}, it was probably "
                          "stopped").format(name=self.application.name))
            yield 100

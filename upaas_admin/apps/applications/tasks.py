# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging
from socket import gethostname

from mongoengine import StringField, ReferenceField

from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError
from upaas import processes

from upaas_admin.config import load_main_config
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.applications.models import Package
from upaas_admin.apps.tasks.base import ApplicationTask, PackageTask
from upaas_admin.apps.tasks.registry import register


log = logging.getLogger(__name__)


@register
class BuildPackageTask(ApplicationTask):

    application = ReferenceField('Application', dbref=False, required=True)
    metadata = StringField(required=True)
    system_filename = StringField()

    def job(self):

        try:
            metadata_obj = MetadataConfig.from_string(self.metadata)
        except ConfigurationError:
            log.error(u"Invalid app metadata")
            raise Exception()

        upaas_config = load_main_config()
        if not upaas_config:
            log.error(u"Missing uPaaS configuration")
            raise Exception()

        log.info(u"Starting build task with parameters app_id=%s, "
                 u"system_filename=%s" % (self.application.safe_id,
                                          self.system_filename))

        build_result = None
        try:
            builder = Builder(upaas_config, metadata_obj)
            for result in builder.build_package(
                    system_filename=self.system_filename):
                log.info("Build progress: %d%%" % result.progress)
                yield result.progress
                build_result = result
        except exceptions.BuildError:
            log.error(u"Build failed")
            raise Exception()

        log.info(u"Build completed")
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
                      distro_arch=build_result.distro_arch)
        pkg.save()
        log.info(u"Package saved with id %s" % pkg.id)

        self.application.reload()
        self.application.packages.append(pkg)
        self.application.current_package = pkg
        self.application.save()
        log.info(u"Application '%s' updated" % self.application.name)
        self.application.update_application()
        self.application.trim_package_files()


@register
class StartPackageTask(PackageTask):

    def job(self):

        if not self.application.run_plan:
            log.error(u"Missing run plan, cannot start "
                      u"'%s'" % self.application.name)
            raise(u"Missing run plan for '%s'" % self.application.name)

        log.info(u"Starting application '%s' using package '%s'" % (
            self.application.name, self.package.safe_id))

        try:
            self.package.unpack()
        except UnpackError, e:
            log.error(u"Unpacking failed: %s" % e)
            raise Exception(u"Unpacking package failed: %s" % e)
        else:
            yield 75

        self.package.save_vassal_config(self.backend)
        # TODO handle backend start task failure with rescue code
        yield 100


@register
class StopPackageTask(PackageTask):

    def job(self):
        def _remove_pkg_dir(directory):
            log.info(u"Removing package directory '%s'" % directory)
            try:
                processes.kill_and_remove_dir(directory)
            except OSError, e:
                log.error(u"Exception during package directory cleanup: "
                          u"%s" % e)

        if os.path.isfile(self.application.vassal_path):
            log.info(u"Removing vassal config file "
                     u"'%s'" % self.application.vassal_path)
            try:
                os.remove(self.application.vassal_path)
            except OSError, e:
                log.error(u"Can't remove vassal config file at '%s': %s" % (
                    self.application.vassal_path, e))
                raise
        else:
            log.error(u"Vassal config file for application '%s' not found at "
                      u"'%s" % (self.application.safe_id,
                                self.application.vassal_path))
        yield 10

        if os.path.isdir(self.package.package_path):
            _remove_pkg_dir(self.package.package_path)
        else:
            log.info(u"Package directory not found at "
                     u"'%s'" % self.package.package_path)
        yield 75

        log.info(u"Checking for old application packages")
        for oldpkg in self.application.packages:
            if os.path.isdir(oldpkg.package_path):
                _remove_pkg_dir(oldpkg.package_path)

        log.info(u"Application '%s' stopped" % self.application.name)
        yield 100

    def cleanup(self):
        if self.application.run_plan:
            log.info(u"Removing '%s' run plan" % self.application.name)
            self.application.run_plan.delete()


@register
class UpgradePackageTask(PackageTask):
    #TODO add graceful update

    def job(self):
        try:
            self.package.unpack()
        except UnpackError:
            log.error(u"Unpacking failed")
            raise
        yield 50

        self.package.save_vassal_config(self.backend)
        yield 75
        self.package.cleanup_application_packages()
        yield 100


@register
class UpdateVassalTask(PackageTask):
    #TODO add graceful update

    def job(self):
        self.package.save_vassal_config(self.backend)
        yield 75
        self.package.cleanup_application_packages()
        yield 100

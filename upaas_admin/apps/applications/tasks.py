# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging
from socket import gethostname

from mongoengine import StringField, ReferenceField

from django.utils.translation import ugettext_lazy as _

from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError
from upaas import processes

from upaas_admin.config import load_main_config
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.applications.models import Package
from upaas_admin.apps.tasks.base import ApplicationTask, PackageTask
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.tasks.registry import register


log = logging.getLogger(__name__)


#TODO translations

@register
class BuildPackageTask(ApplicationTask):

    application = ReferenceField('Application', dbref=False, required=True)
    metadata = StringField(required=True)
    system_filename = StringField()

    def generate_title(self):
        if self.system_filename:
            return _(u"Building new package for {name}").format(
                name=self.application.name)
        else:
            return _(u"Building new fresh package for {name}").format(
                name=self.application.name)

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
                log.debug("Build progress: %d%%" % result.progress)
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
        self.application.upgrade_application()
        self.application.trim_package_files()


@register
class StartPackageTask(PackageTask):

    def generate_title(self):
        return _(u"Starting {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):

        if not self.application.run_plan:
            log.error(u"Missing run plan, cannot start "
                      u"'%s'" % self.application.name)
            raise Exception(u"Missing run plan for "
                            u"'%s'" % self.application.name)

        log.info(u"Starting application '%s' using package '%s'" % (
            self.application.name, self.package.safe_id))

        if not os.path.exists(self.package.package_path):
            try:
                self.package.unpack()
            except UnpackError, e:
                log.error(u"Unpacking failed: %s" % e)
                raise Exception(u"Unpacking package failed: %s" % e)
        else:
            log.warning(u"Package already exists: "
                        u"%s" % self.package.package_path)
        yield 50

        self.package.save_vassal_config(self.backend)
        # TODO handle backend start task failure with rescue code

        self.wait_until_running()
        yield 100


@register
class StopPackageTask(PackageTask):

    def generate_title(self):
        return _(u"Stopping {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

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
            log.warning(u"Vassal config file for application '%s' not found "
                        u"at '%s" % (self.application.safe_id,
                                     self.application.vassal_path))
        yield 10

        if os.path.isdir(self.package.package_path):
            _remove_pkg_dir(self.package.package_path)
        else:
            log.warning(u"Package directory not found at "
                        u"'%s'" % self.package.package_path)
        yield 75

        log.info(u"Checking for old application packages")
        for oldpkg in self.application.packages:
            if os.path.isdir(oldpkg.package_path):
                _remove_pkg_dir(oldpkg.package_path)

        self.backend.delete_application_ports(self)
        ApplicationRunPlan.objects(id=self.application.run_plan.id).update_one(
            pull__backends=self.backend)

        log.info(u"Application '%s' stopped" % self.application.name)
        yield 100

    def cleanup(self):
        run_plan = self.application.run_plan
        if run_plan and not run_plan.backends:
            log.info(u"Removing '%s' run plan" % self.application.name)
            run_plan.delete()


@register
class UpgradePackageTask(PackageTask):

    def generate_title(self):
        return _(u"Upgrading {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        try:
            self.package.unpack()
        except UnpackError:
            log.error(u"Unpacking failed")
            raise
        yield 40

        self.package.save_vassal_config(self.backend)
        yield 75

        self.wait_until_running()
        yield 95

        self.package.cleanup_application_packages()
        yield 100


@register
class UpdateVassalTask(PackageTask):

    def generate_title(self):
        return _(u"Updating {name} configuration on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        self.package.save_vassal_config(self.backend)
        yield 50

        self.wait_until_running()
        yield 95

        self.package.cleanup_application_packages()
        yield 100

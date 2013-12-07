# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


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
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.tasks.registry import register


log = logging.getLogger(__name__)


#TODO translations

@register
class BuildPackageTask(ApplicationTask):

    application = ReferenceField('Application', dbref=False, required=True)
    metadata = StringField(required=True)
    force_fresh = BooleanField(default=False)

    def generate_title(self):
        if self.force_fresh:
            return _(u"Building new fresh package for {name}").format(
                name=self.application.name)
        else:
            return _(u"Building new package for {name}").format(
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

        system_filename = None
        if not self.force_fresh and self.application.current_package:
            system_filename = self.application.current_package.filename
            log.info(_(u"Using current application package {pkg} as "
                       u"parent").format(
                pkg=self.application.current_package.safe_id))

        log.info(u"Starting build task with parameters app_id=%s, "
                 u"force_fresh=%s" % (self.application.safe_id,
                                      self.force_fresh))

        build_result = None
        try:
            builder = Builder(upaas_config, metadata_obj)
            for result in builder.build_package(
                    system_filename=system_filename):
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
class StartApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _(u"Starting {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):

        if not self.application.run_plan:
            log.error(u"Missing run plan, cannot start "
                      u"'%s'" % self.application.name)
            raise Exception(u"Missing run plan for "
                            u"'%s'" % self.application.name)

        run_plan = self.application.run_plan

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            if backend_conf.package.id != self.application.current_package.id:
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
            log.info(u"Starting application '%s' using package '%s'" % (
                self.application.name, backend_conf.package.safe_id))

            if not os.path.exists(backend_conf.package.package_path):
                try:
                    backend_conf.package.unpack()
                except UnpackError, e:
                    log.error(u"Unpacking failed: %s" % e)
                    raise Exception(u"Unpacking package failed: %s" % e)
            else:
                log.warning(u"Package already exists: "
                            u"%s" % backend_conf.package.package_path)
            yield 50

            backend_conf.package.save_vassal_config(backend_conf)
            # TODO handle backend start task failure with rescue code

            self.wait_until_running()
            yield 100
        else:
            log.error(_(u"Backend {backend} missing in run plan for "
                        u"{name}").format(backend=self.backend.name,
                                          name=self.application.name))
            yield 100


@register
class StopApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _(u"Stopping {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
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

        self.wait_until_stopped()
        yield 75

        run_plan = self.application.run_plan
        if run_plan:
            run_plan.remove_backend_settings(self.backend)
        else:
            log.warning(_(u"Missing run plan for {name}, already "
                          u"stopped?").format(name=self.application.name))

        self.application.remove_unpacked_packages()
        log.info(u"Application '%s' stopped" % self.application.name)
        yield 100

    def cleanup(self):
        run_plan = self.application.run_plan
        if run_plan and not run_plan.backends:
            log.info(u"Removing '%s' run plan" % self.application.name)
            run_plan.delete()


@register
class UpgradeApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _(u"Upgrading {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        run_plan = self.application.run_plan
        if not run_plan:
            msg = unicode(_(u"Missing run plan for {name}, cannot "
                          u"upgrade").format(name=self.application.name))
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
                log.error(u"Unpacking failed")
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
            log.warning(_(u"No run plan for {name}, it was probably "
                          u"stopped").format(name=self.application.name))
            yield 100


@register
class UpdateVassalTask(ApplicationBackendTask):

    def generate_title(self):
        return _(u"Updating {name} configuration on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        run_plan = self.application.run_plan
        if not run_plan:
            msg = unicode(_(u"Missing run plan for {name}, application was "
                            u"already stopped?").format(
                name=self.application.name))
            log.warning(msg)
            yield 100
            raise StopIteration

        backend_conf = self.application.run_plan.backend_settings(self.backend)
        if backend_conf:

            if backend_conf.package.id != self.application.current_package.id:
                log.info(_(u"Old package on backend, running upgrade"))
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
            try:
                backend_conf.package.unpack()
            except UnpackError:
                log.error(u"Unpacking failed")
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
            log.warning(_(u"No run plan for {name}, it was probably "
                          u"stopped").format(name=self.application.name))
            yield 100

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from mongoengine import StringField, ReferenceField

from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError
from upaas_admin.apps.applications.exceptions import UnpackError

from upaas_admin.apps.applications.models import Package, Application
from upaas_admin.apps.tasks.models import Task


log = logging.getLogger(__name__)


class BuildPackageTask(Task):

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
                      interpreter_name=metadata_obj.interpreter.type,
                      interpreter_version=build_result.interpreter_version,
                      bytes=build_result.bytes,
                      filename=build_result.filename,
                      checksum=build_result.checksum,
                      parent=build_result.parent,
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


class BackendTask(Task):

    backend = ReferenceField('BackendServer', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
    }


class StartPackageTask(BackendTask):

    package = ReferenceField('Package', dbref=False, required=True)

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

        log.info(u"Generating uWSGI vassal configuration")
        options = self.package.generate_uwsgi_config(self.backend)

        if not options:
            log.error(u"Couldn't generate vassal configuration")
            return

        log.info(u"Saving vassal configuration to "
                 u"'%s'" % self.application.vassal_path)
        with open(self.application.vassal_path, 'w') as vassal:
            vassal.write('\n'.join(options))

        log.info(u"Vassal saved")

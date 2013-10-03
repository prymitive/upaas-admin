# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError

from upaas_admin.apps.applications.models import Package, Application


log = logging.getLogger(__name__)


class BuildPackageTask:

    def run(self, params):
        metadata = params.get('metadata')
        app_id = params.get('app_id')
        system_filename = params.get('system_filename')

        if not metadata or not app_id:
            log.error(u"Missing metadata or app_id in %s" % params)
            raise ValueError()

        try:
            metadata_obj = MetadataConfig.from_string(metadata)
        except ConfigurationError:
            log.error(u"Invalid app metadata")
            raise Exception()

        upaas_config = load_main_config()
        if not upaas_config:
            log.error(u"Missing uPaaS configuration")
            raise Exception()

        log.info(u"Starting build task with parameters app_id=%s, "
                 u"system_filename=%s" % (app_id, system_filename))

        build_result = None
        try:
            builder = Builder(upaas_config, metadata_obj)
            for result in builder.build_package(
                    system_filename=system_filename):
                log.info("Build progress: %d%%" % result.progress)
                yield result.progress
                build_result = result
        except exceptions.BuildError:
            log.error(u"Build failed")
            raise Exception()

        log.info(u"Build completed")
        pkg = Package(metadata=metadata,
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

        if app_id:
            app = Application.objects(id=app_id).first()
            if app:
                # register package
                app.packages.append(pkg)
                app.current_package = pkg
                app.save()
                log.info(u"Application '%s' updated" % app.name)
                app.update_application()
            else:
                log.error(u"Application with id '%s' not found" % app_id)

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import absolute_import

import os
import tempfile
import shutil

from celery import task, current_task
from celery.utils.log import get_task_logger
from celery.exceptions import Ignore
from celery.states import FAILURE

from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError
from upaas.storage.utils import find_storage_handler
from upaas.storage.exceptions import StorageError
from upaas import tar

from upaas_admin.apps.applications.models import Package, Application
from upaas_admin.apps.servers.models import BackendServer


log = get_task_logger(__name__)


@task
def build_package(metadata, app_id=None, system_filename=None):
    try:
        metadata_obj = MetadataConfig.from_string(metadata)
    except ConfigurationError:
        log.error(u"Invalid app metadata")
        build_package.update_state(state=FAILURE)
        raise Ignore()

    upaas_config = load_main_config()
    if not upaas_config:
        log.error(u"Missing uPaaS configuration")
        build_package.update_state(state=FAILURE)
        raise Ignore()

    build_result = None
    try:
        builder = Builder(upaas_config, metadata_obj)
        for result in builder.build_package(system_filename=system_filename):
            log.info("Build progress: %d%%" % result.progress)
            current_task.update_state(state='PROGRESS',
                                      meta={'current': result.progress,
                                            'total': 100})
            build_result = result
    except exceptions.BuildError:
        log.error(u"Build failed")
        build_package.update_state(state=FAILURE)
        raise Ignore()

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
        else:
            log.error(u"Application with id '%s' not found" % app_id)

    return pkg


@task
def start_application(metadata, package_id):
    def _cleanup(*args):
        for directory in args:
            if os.path.isdir(directory):
                log.info(u"Removing directory '%s'" % directory)
                shutil.rmtree(directory)

    pkg = Package.objects(id=package_id).first()
    if not pkg:
        log.error(u"Package with id '%s' not found" % package_id)
        start_application.update_state(state=FAILURE)
        raise Ignore()

    upaas_config = load_main_config()
    if not upaas_config:
        log.error(u"Missing uPaaS configuration")
        start_application.update_state(state=FAILURE)
        raise Ignore()

    # directory is encoded into string to prevent unicode errors
    directory = tempfile.mkdtemp(dir=upaas_config.paths.workdir,
                                 prefix="upaas_package_").encode("utf-8")

    storage = find_storage_handler(upaas_config)
    if not storage:
        log.error(u"Storage handler '%s' not "
                  u"found" % upaas_config.storage.handler)

    workdir = os.path.join(directory, "system")
    pkg_path = os.path.join(directory, pkg.filename)
    final_path = os.path.join(upaas_config.paths.apps, str(pkg.id))

    if os.path.exists(final_path):
        log.error(u"Package directory already exists: %s" % final_path)
        start_application.update_state(state=FAILURE)
        raise Ignore()

    log.info(u"Fetching package '%s'" % pkg.filename)
    try:
        storage.get(pkg.filename, pkg_path)
    except StorageError:
        log.error(u"Storage error while fetching package '%s'" % pkg.filename)
        start_application.update_state(state=FAILURE)
        _cleanup(directory)
        raise Ignore()

    log.info(u"Unpacking package")
    os.mkdir(workdir, 0755)
    if not tar.unpack_tar(pkg_path, workdir):
        log.error(u"Error while unpacking package to '%s'" % workdir)
        start_application.update_state(state=FAILURE)
        _cleanup(directory)
        raise Ignore()

    log.info(u"Package unpacked, moving into '%s'" % final_path)
    try:
        shutil.move(workdir, final_path)
    except shutil.Error, e:
        log.error(u"Error while moving unpacked package to final "
                  u"destination: %s" % e)
        start_application.update_state(state=FAILURE)
        _cleanup(directory, final_path)
        raise Ignore()
    log.info(u"Package moved")
    _cleanup(directory)

    backend = BackendServer.get_local_backend()
    log.info(u"Generating uWSGI vassal configuration")
    options = pkg.generate_uwsgi_config(backend)

    vassal_path = os.path.join(upaas_config.paths.vassals,
                               '%s.ini' % pkg.application.id)
    log.info(u"Saving vassal configuration to '%s'" % vassal_path)
    with open(vassal_path, 'w') as vassal:
        vassal.write('\n'.join(options))

    log.info(u"Vassal saved")

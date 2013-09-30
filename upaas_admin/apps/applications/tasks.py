# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import absolute_import

import os
import time

from celery import task, current_task
from celery.utils.log import get_task_logger
from celery.exceptions import Ignore
from celery.states import FAILURE

from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError
from upaas import processes

from upaas_admin.apps.applications.models import Package, Application
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.servers.models import BackendServer
# FIXME mongoengine complains that User model is not registered without it
from upaas_admin.apps.users.models import User
from upaas_admin.apps.tasks.constants import STATE_PROGRESS

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

    log.info(u"Starting build task with parameters app_id=%s, "
             u"system_filename=%s" % (app_id, system_filename))

    build_result = None
    try:
        builder = Builder(upaas_config, metadata_obj)
        for result in builder.build_package(system_filename=system_filename):
            log.info("Build progress: %d%%" % result.progress)
            current_task.update_state(state=STATE_PROGRESS,
                                      meta={'progress': result.progress})
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
            app.update_application()
        else:
            log.error(u"Application with id '%s' not found" % app_id)

    return pkg.safe_id


@task
def start_application(package_id):
    pkg = Package.objects(id=package_id).first()
    if not pkg:
        log.error(u"Package with id '%s' not found" % package_id)
        start_application.update_state(state=FAILURE)
        raise Ignore()

    try:
        pkg.unpack()
    except UnpackError:
        log.error(u"Unpacking failed")
        raise Ignore()

    backend = BackendServer.get_local_backend()
    log.info(u"Generating uWSGI vassal configuration")
    options = pkg.generate_uwsgi_config(backend)

    if not options:
        log.error(u"Couldn't generate vassal configuration")
        return

    log.info(u"Saving vassal configuration to "
             u"'%s'" % pkg.application.vassal_path)
    with open(pkg.application.vassal_path, 'w') as vassal:
        vassal.write('\n'.join(options))

    log.info(u"Vassal saved")


@task
def stop_application(package_id):
    def _remove_pkg_dir(directory):
        log.info(u"Removing package directory '%s'" % directory)
        try:
            processes.kill_and_remove_dir(directory)
        except OSError, e:
            log.error(u"Exception during package directory cleanup: %s" % e)

    pkg = Package.objects(id=package_id).first()
    if not pkg:
        log.error(u"Package with id '%s' not found" % package_id)
        stop_application.update_state(state=FAILURE)
        raise Ignore()

    if os.path.isfile(pkg.application.vassal_path):
        log.info(u"Removing vassal config file "
                 u"'%s'" % pkg.application.vassal_path)
        try:
            os.remove(pkg.application.vassal_path)
        except OSError, e:
            log.error(u"Can't remove vassal config file at '%s': %s" % (
                pkg.application.vassal_path, e))
            stop_application.update_state(state=FAILURE)
            raise Ignore()
    else:
        log.error(u"Vassal config file for application '%s' not found at "
                  u"'%s" % (pkg.application.safe_id,
                            pkg.application.vassal_path))

    if os.path.isdir(pkg.package_path):
        _remove_pkg_dir(pkg.package_path)
    else:
        log.info(u"Package directory not found at '%s'" % pkg.package_path)

    log.info(u"Checking for old application packages")
    for oldpkg in pkg.application.packages:
        if os.path.isdir(oldpkg.package_path):
            _remove_pkg_dir(oldpkg.package_path)

    log.info(u"Application stopped")


@task
def update_application(package_id):
    #FIXME refactor it to be more DRY

    pkg = Package.objects(id=package_id).first()
    if not pkg:
        log.error(u"Package with id '%s' not found" % package_id)
        start_application.update_state(state=FAILURE)
        raise Ignore()

    try:
        pkg.unpack()
    except UnpackError:
        log.error(u"Unpacking failed")
        raise Ignore()

    backend = BackendServer.get_local_backend()
    log.info(u"Generating uWSGI vassal configuration")
    options = pkg.generate_uwsgi_config(backend)

    log.info(u"Saving vassal configuration to "
             u"'%s'" % pkg.application.vassal_path)
    with open(pkg.application.vassal_path, 'w') as vassal:
        vassal.write('\n'.join(options))

    log.info(u"Vassal saved")

    log.info(u"Checking for old application packages")
    for oldpkg in pkg.application.packages:
        if oldpkg.id == pkg.id:
            # skip current package!
            continue
        if os.path.isdir(oldpkg.package_path):
            log.info(u"Removing package directory '%s'" % oldpkg.package_path)

            # if there are running pids inside package dir we will need to wait
            # this should only happen during upgrade, when we need to wait
            # for app to reload into new package dir
            pids = processes.directory_pids(oldpkg.package_path)
            while pids:
                log.info(u"Waiting for %d pid(s) in %s to terminate" % (
                    len(pids), oldpkg.package_path))
                time.sleep(2)
                pids = processes.directory_pids(oldpkg.package_path)

            try:
                processes.kill_and_remove_dir(oldpkg.package_path)
            except OSError, e:
                log.error(u"Exception during package directory cleanup: "
                          u"%s" % e)

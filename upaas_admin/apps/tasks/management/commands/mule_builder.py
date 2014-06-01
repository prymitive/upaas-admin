# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging
from datetime import datetime

from django.utils.translation import ugettext as _

from upaas.builder.builder import Builder
from upaas.builder.exceptions import BuildError

from upaas_admin.config import load_main_config
from upaas_admin.apps.applications.constants import NeedsBuildingFlag
from upaas_admin.apps.applications.models import Package
from upaas_admin.apps.tasks.mule import MuleCommand


log = logging.getLogger(__name__)


class Command(MuleCommand):

    mule_name = _('Builder')
    mule_flags = [NeedsBuildingFlag.name]

    def handle_flag(self, flag):

        app = flag.application
        self.app_name = app.name
        current_package = app.current_package
        force_fresh = flag.options.get(
            NeedsBuildingFlag.Options.build_fresh_package, False)
        interpreter_version = flag.options.get(
            NeedsBuildingFlag.Options.build_interpreter_version)

        system_filename = None
        current_revision = None
        if not force_fresh and current_package:
            system_filename = current_package.filename
            current_revision = current_package.revision_id
            interpreter_version = current_package.interpreter_version

        log.info(_("Building new package for {name} [{id}]").format(
            name=app.name, id=app.safe_id))

        task = self.create_task(app, flag.title, flag=flag.name)

        metadata = flag.application.metadata
        metadata_obj = flag.application.metadata_config
        if not metadata or not metadata_obj:
            log.error(_("Missing or invalid application metadata"))
            self.fail_flag(flag, task)

        upaas_config = load_main_config()
        if not upaas_config:
            log.error(_("Missing or invalid uPaaS configuration"))
            self.fail_flag(flag, task)

        log.info(_("Building package for application {name} "
                   "[{id}]").format(name=flag.application.name,
                                    id=flag.application.safe_id))
        log.info(_("Fresh package: {fresh}").format(fresh=force_fresh))
        log.info(_("Base image: {name}").format(name=system_filename))
        log.info(_("Interpreter version: {ver}").format(
            ver=interpreter_version))
        log.info(_("Current revision: {rev}").format(
            rev=current_revision))

        env = {}
        for feature in app.feature_helper.load_enabled_features():
            env = feature.update_env(app, env)

        build_result = None
        try:
            builder = Builder(upaas_config, metadata_obj)
            for result in builder.build_package(
                    system_filename=system_filename,
                    interpreter_version=interpreter_version,
                    current_revision=current_revision,
                    env=env):
                log.debug(_("Build progress: {proc}%").format(
                    proc=result.progress))
                build_result = result
                task.update(set__progress=result.progress)
        except BuildError:
            self.fail_flag(flag, task)
        else:
            self.create_package(app, task, metadata_obj, metadata,
                                build_result, current_package)
        self.mark_task_successful(task)

    def create_package(self, app, task, metadata_obj, metadata, build_result,
                       parent_package):
        log.info("Building completed, saving package")
        pkg = Package(metadata=metadata,
                      application=app,
                      task=task,
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
        log.info(_("Package saved with id {id}").format(id=pkg.safe_id))

        app.update(add_to_set__packages=pkg, set__current_package=pkg)
        app.reload()
        app.upgrade_application()
        app.trim_package_files()

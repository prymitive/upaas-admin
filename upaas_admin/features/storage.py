# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import logging
from pwd import getpwnam, getpwuid
from grp import getgrnam, getgrgid

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from upaas.config.base import FSPathEntry

from upaas_admin.features.base import Feature


log = logging.getLogger(__name__)


class StorageFeature(Feature):

    configuration_schema = {
        "path": FSPathEntry(required=True),
        "mountpoint": FSPathEntry(required=True),
    }

    def application_dir(self, application):
        return os.path.join(self.settings.path, application.safe_id)

    def chown(self, directory):
        try:
            uid = int(settings.UPAAS_CONFIG.apps.uid)
        except:
            user = getpwnam(settings.UPAAS_CONFIG.apps.uid)
        else:
            user = getpwuid(uid)

        try:
            gid = int(settings.UPAAS_CONFIG.apps.gid)
        except:
            group = getgrnam(settings.UPAAS_CONFIG.apps.uid)
        else:
            group = getgrgid(gid)

        os.chown(directory, user.pw_uid, group.gr_gid)

    def update_vassal(self, application, options):
        app_dir = self.application_dir(application)
        options.append('namespace-keep-mount = %s:%s\n' % (
            app_dir, self.settings.mountpoint))
        return options

    def after_unpack(self, application, workdir):
        app_dir = self.application_dir(application)
        if not os.path.exists(app_dir):
            log.info(_("Creating {name} storage dir: {path}").format(
                name=application.name, path=app_dir))
            os.mkdir(app_dir, 0o700)
            try:
                self.chown(app_dir)
            except Exception as e:
                log.error(_("Can't chown application storage directory: "
                            "{e}").format(e=e))

        mountpoint = os.path.join(
            workdir, self.settings.mountpoint.lstrip('/'))
        if not os.path.exists(mountpoint):
            log.info(_("Creating {name} mountpoint dir: {path}").format(
                name=application.name, path=self.mountpoint))
            os.mkdir(mountpoint, 0o700)
            try:
                self.chown(mountpoint)
            except Exception as e:
                log.error(_("Can't chown application mountpoint directory: "
                            "{e}").format(e=e))

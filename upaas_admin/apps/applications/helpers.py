# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas_admin.apps.applications import constants as flags


class ApplicationStateHelper(object):

    def __init__(self, application):
        self.app = application

    def pending_backends(self, flag):
        return self.app.flags.filter(name=flag,
                                     pending_backends__exists=True).first()

    @property
    def needs_building(self):
        print((self.app.flags, self.app.flags.filter(
            name=flags.NeedsBuildingFlag.name, pending__ne=False).first()))
        return self.app.flags.filter(name=flags.NeedsBuildingFlag.name,
                                     pending__ne=False).first()

    @property
    def needs_starting(self):
        return self.pending_backends(flags.IsStartingFlag.name)

    @property
    def needs_restarting(self):
        return self.pending_backends(flags.NeedsRestartFlag.name)

    @property
    def needs_stopping(self):
        return self.pending_backends(flags.NeedsStoppingFlag.name)

    @property
    def needs_upgrade(self):
        return self.pending_backends(flags.NeedsUpgradeFlag.name)

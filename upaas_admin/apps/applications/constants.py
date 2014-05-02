# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


class NeedsBuildingFlag:
    name = 'NEEDS_BUILDING'
    title = _('Building package')

    class Options:
        build_fresh_package = 'BUILD_FRESH_PACKAGE'
        build_interpreter_version = 'BUILD_INTERPRETER_VERSION'


class IsStartingFlag:
    name = 'IS_STARTING'
    title = _('Starting application instance')


class NeedsUpgradeFlag:
    name = 'NEEDS_UPGRADE'
    title = _('Upgrading application instance')


class NeedsStoppingFlag:
    name = 'NEEDS_STOPPING'
    title = _('Stopping application instance')


class NeedsRestartFlag:
    name = 'NEEDS_RESTART'
    title = _('Restarting application instance')


class NeedsRemovingFlag:
    name = 'NEEDS_REMOVING'
    title = _('Removing application instance')


FLAGS_BY_NAME = {
    NeedsBuildingFlag.name: NeedsBuildingFlag,
    IsStartingFlag.name: IsStartingFlag,
    NeedsUpgradeFlag.name: NeedsUpgradeFlag,
    NeedsStoppingFlag.name: NeedsStoppingFlag,
    NeedsRestartFlag.name: NeedsRestartFlag,
    NeedsRemovingFlag.name: NeedsRemovingFlag,
}


# list of flags that should execute single task on single backend
SINGLE_SHOT_FLAGS = [NeedsBuildingFlag.name]

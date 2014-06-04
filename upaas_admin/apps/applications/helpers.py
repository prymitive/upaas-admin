# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from upaas.utils import load_handler
from upaas.config.base import ConfigurationError

from upaas_admin.apps.applications import constants as flags


log = logging.getLogger(__name__)


class ApplicationStateHelper(object):

    def __init__(self, application):
        self.app = application

    def pending_backends(self, flag):
        return self.app.flags.filter(name=flag,
                                     pending_backends__exists=True).first()

    @property
    def needs_building(self):
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

    @property
    def needs_rescheduling(self):
        return self.app.flags.filter(name=flags.NeedsReschedulingFlag.name,
                                     pending__ne=False).first()


class ApplicationFeatureHelper(object):

    def __init__(self, application):
        self.app = application

    @property
    def enabled_features(self):
        features = {}
        metadata = self.app.metadata_config
        for name, config in settings.UPAAS_CONFIG.apps.features.items():
            value = False
            if metadata.features:
                value = metadata.features.get(name, False)
            if config.enabled and value:
                features[name] = [config, value]
        return features

    def load_feature(self, name, config, value):
        try:
            return load_handler(config.handler, name, config.settings, value)
        except ConfigurationError as e:
            log.error(_("Error while loading {name} feature: {msg}").format(
                name=name, msg=e))

    def load_enabled_features(self):
        features = []
        for name, params in self.enabled_features.items():
            config, value = params
            feature = self.load_feature(name, config, value)
            if feature:
                features.append(feature)
            else:
                log.error(_("{name} feature failed to load").format(name=name))
        return features

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext as _

from upaas.config.base import (Config, ConfigurationError, StringEntry,
                               IntegerEntry)

from upaas_admin.features.base import Feature


log = logging.getLogger(__name__)


class CronEntryConfig(Config):

    schema = {
        "command": StringEntry(required=True),
        "minute": IntegerEntry(min_value=0, max_value=59, default=-1),
        "hour": IntegerEntry(min_value=0, max_value=23, default=-1),
        "day": IntegerEntry(min_value=1, max_value=31, default=-1),
        "month": IntegerEntry(min_value=1, max_value=12, default=-1),
        "weekday": IntegerEntry(min_value=1, max_value=7, default=-1),
    }


class CronFeature(Feature):

    def parse_crons(self):
        crons = []
        for item in self.value:
            try:
                cron = CronEntryConfig(item)
            except ConfigurationError as e:
                log.error(_('Invalid cron configuration in {item}: '
                            '{e}').format(item=item, e=e))
            else:
                crons.append('cron = %d %d %d %d %d %s' % (
                    cron.minute, cron.hour, cron.day, cron.month, cron.weekday,
                    cron.command))
        return crons

    def update_vassal(self, application, options):
        for cron in self.parse_crons():
            options.append(cron)
        return options

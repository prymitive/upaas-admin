# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime
import logging

from mongoengine import *

from django.utils.translation import ugettext_lazy as _


log = logging.getLogger(__name__)


class Package(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    application = ReferenceField('Application', reverse_delete_rule=DENY,
                                 dbref=False)
    metadata = StringField(help_text=_('Application metadata'))

    bytes = LongField(required=True)
    checksum = StringField(required=True)

    distro_name = StringField(required=True)
    distro_version = StringField(required=True)
    distro_arch = StringField(required=True)

    meta = {
        'indexes': [
            {'fields': ['application']}
        ]
    }

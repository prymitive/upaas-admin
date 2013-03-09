# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime

from mongoengine import *

from django.utils.translation import ugettext_lazy as _


class ApplicationMetadata(EmbeddedDocument):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    content = StringField(required=True)


class Application(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=100, unique=True,
                       verbose_name=_('name'), help_text=_('Application name'))
    owners = ListField(ReferenceField('User', reverse_delete_rule=DENY,
                                      dbref=False))
    metadata = ListField(EmbeddedDocumentField(ApplicationMetadata))

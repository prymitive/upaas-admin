# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime

import mongoengine

from django.utils.translation import ugettext_lazy as _


class ApplicationMetadata(mongoengine.EmbeddedDocument):
    date_created = mongoengine.DateTimeField(
        required=True, default=datetime.datetime.now)
    content = mongoengine.StringField(required=True)


class Application(mongoengine.Document):
    date_created = mongoengine.DateTimeField(
        required=True, default=datetime.datetime.now)
    name = mongoengine.StringField(
        required=True, max_length=100, unique=True, verbose_name=_('name'),
        help_text=_('Application name'))
    comments = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(ApplicationMetadata))

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from upaas_tasks.build import build_package as build_package_task


class Application(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=100, unique=True,
                       verbose_name=_('name'), help_text=_('Application name'))
    owner = ListField(ReferenceField('User', reverse_delete_rule=DENY,
                                     dbref=False))
    metadata = StringField(help_text=_('Application metadata'))

    meta = {
        'indexes': [
            {'fields': ['date_created', 'name', 'owner']}
        ]
    }

    def build_package(self, force_fresh=False):
        task = build_package_task.delay(self.metadata, force_fresh=force_fresh)
        return task.task_id

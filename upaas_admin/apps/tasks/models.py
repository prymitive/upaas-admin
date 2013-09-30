# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime

from mongoengine import ReferenceField, StringField, DateTimeField, Document


class Task(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)

    task_id = StringField(required=True)
    title = StringField()
    user = ReferenceField('User', dbref=False)
    application = ReferenceField('Application', dbref=False)

    meta = {
        'indexes': [
            {'fields': ['application', 'task_id']}
        ],
        'ordering': ['-date_created'],
    }

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import sys
import datetime
import logging

from mongoengine import (StringField, DateTimeField, IntField, ListField,
                         ReferenceField, Document, EmbeddedDocument,
                         EmbeddedDocumentField, NULLIFY)

from upaas_admin.apps.tasks.constants import *
from upaas_admin.apps.servers.models import BackendServer


log = logging.getLogger(__name__)


class MongoLogHandler(logging.StreamHandler):

    def __init__(self, task, flush_count=10, flush_time=3, *args,
                 **kwargs):
        if sys.version_info[:2] > (2, 6):
            super(MongoLogHandler, self).__init__(*args, **kwargs)
        else:
            logging.StreamHandler.__init__(self, *args, **kwargs)

        self.task = task
        self.flush_count = flush_count
        self.flush_time = flush_time

        self.messages = []
        self.last_flush = datetime.datetime.now()

    def flush(self):
        self.task.__class__.objects(id=self.task.id).update_one(
            push_all__messages=self.messages)
        self.messages = []
        self.last_flush = datetime.datetime.now()

    def emit(self, record):
        # skip debug messages
        if record.levelno < logging.INFO:
            return
        msg = TaskMessage(
            timestamp=datetime.datetime.fromtimestamp(record.created),
            source=record.name, level=record.levelno, message=record.msg)
        self.messages.append(msg)
        if record.__dict__.get('force_flush'):
            self.flush()
        elif len(self.messages) >= self.flush_count:
            self.flush()
        elif datetime.datetime.now() - self.last_flush >= datetime.timedelta(
                seconds=self.flush_time):
            self.flush()


class TaskMessage(EmbeddedDocument):

    timestamp = DateTimeField(required=True, default=datetime.datetime.now)
    source = StringField(required=True)
    level = IntField(required=True)
    message = StringField(required=True)


class Task(Document):

    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    date_finished = DateTimeField()
    application = ReferenceField('Application')
    flag = StringField()
    title = StringField(required=True)
    status = StringField(required=True, choices=STATUS_CHOICES,
                         default=TaskStatus.running)
    progress = IntField(min_value=0, max_value=100, default=0)
    messages = ListField(EmbeddedDocumentField(TaskMessage))
    backend = ReferenceField(BackendServer, reverse_delete_rule=NULLIFY)
    pid = IntField(required=True)

    meta = {
        'ordering': ['-date_finished', '-date_created'],
        'indexes': ['id', 'date_created', 'date_finished', 'application',
                    'flag', 'status'],
    }

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        self.log_handler = None

    @property
    def safe_id(self):
        return str(self.id)

    @property
    def is_running(self):
        return self.status == TaskStatus.running

    @property
    def is_failed(self):
        return self.status == TaskStatus.failed

    @property
    def is_successful(self):
        return self.status == TaskStatus.successful

    @property
    def is_finished(self):
        return not self.is_running

    @property
    def icon_class(self):
        if self.is_running:
            return ICON_STARTED
        elif self.is_failed:
            return ICON_FAILED
        elif self.is_successful:
            return ICON_SUCCESSFUL
        return ICON_UNKNOWN

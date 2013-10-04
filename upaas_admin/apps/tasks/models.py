# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import datetime
import logging
from socket import gethostname

from mongoengine import (ReferenceField, StringField, DateTimeField, IntField,
                         ListField, Document)

from django.utils.translation import ugettext_lazy as _

from upaas_admin.apps.tasks.constants import STATUS_CHOICES, TaskStatus


log = logging.getLogger(__name__)


class Task(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    date_finished = DateTimeField()
    title = StringField(required=True)
    user = ReferenceField('User', dbref=False)
    application = ReferenceField('Application', dbref=False)
    status = StringField(required=True, choices=STATUS_CHOICES,
                         default=TaskStatus.pending)
    progress = IntField(min_value=0, max_value=100, default=0)
    messages = ListField(StringField())
    locked_since = DateTimeField()
    locked_by_backend = StringField()
    locked_by_pid = IntField()

    worker_hostname = gethostname()
    worker_pid = os.getpid()

    meta = {
        'allow_inheritance': True,
        'indexes': [
            {'fields': ['application', 'user']},
        ],
        'ordering': ['-date_created'],
    }

    def unlock_task(self):
        self.reload()
        self.date_finished = datetime.datetime.now()
        del self.locked_by_backend
        del self.locked_by_pid
        del self.locked_since

    def fail_task(self):
        self.unlock_task()
        self.status = TaskStatus.failed
        self.save()

    def execute(self):
        try:
            for progress in self.job():
                log.info(u"Task progress: %d%%" % progress)
                self.update(set__progress=progress)
        except Exception, e:
            log.error(u"Task %s failed: %s" % (self.id, e))
            self.fail_task()
        else:
            self.unlock_task()
            self.status = TaskStatus.successful
            self.save()

    def job(self):
        raise NotImplementedError(_(u"Task has no job defined!"))

    @classmethod
    def pop(cls, **kwargs):
        cls.objects(status=TaskStatus.pending, **kwargs).update_one(
            set__locked_by_backend=cls.worker_hostname,
            set__locked_by_pid=cls.worker_pid,
            set__locked_since=datetime.datetime.now())
        return cls.objects(locked_by_backend=cls.worker_hostname,
                           locked_by_pid=cls.worker_pid).first()

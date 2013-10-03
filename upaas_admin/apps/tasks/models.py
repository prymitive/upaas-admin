# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime
import uuid
import logging

from mongoengine import (ReferenceField, StringField, DateTimeField, IntField,
                         ListField, DictField, Document)

from upaas_admin.apps.tasks.constants import STATUS_CHOICES, TaskStatus


log = logging.getLogger(__name__)


class Task(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    date_finished = DateTimeField()
    title = StringField(required=True)
    user = ReferenceField('User', dbref=False)
    application = ReferenceField('Application', dbref=False)
    queue = StringField(required=True)
    status = StringField(required=True, choices=STATUS_CHOICES,
                         default=TaskStatus.pending)
    progress = IntField(min_value=0, max_value=100, default=0)
    messages = ListField(StringField())
    locked_by = StringField()
    locked_since = DateTimeField()
    task_module = StringField(required=True)
    task_class = StringField(required=True)
    task_params = DictField()

    meta = {
        'allow_inheritance': True,
        'indexes': [
            {'fields': ['application', 'user', 'queue']},
            {'fields': ['locked_by'], 'unique': True}
        ],
        'ordering': ['-date_created'],
    }

    def unlock_task(self):
        self.date_finished = datetime.datetime.now()
        del self.locked_by
        del self.locked_since

    def fail_task(self):
        self.unlock_task()
        self.status = TaskStatus.failed
        self.save()

    def execute(self):
        log.info(u"Executing task '%s' using %s.%s, params: %s" % (
            self.id, self.task_module, self.task_class,
            self.task_params.keys()))
        task_class = None
        try:
            exec("from %s import %s as task_class" % (
                self.task_module, self.task_class))
        except ImportError:
            log.error(u"Task class not found: %s.%s" % self.task_module,
                      self.task_class)
            return self.fail_task()
        else:
            params = {}
            params.update(self.task_params)
            if self.application:
                params['app_id'] = self.application.safe_id
            try:
                for progress in task_class().run(params):
                    log.info(u"Task progress: %d%%" % progress)
                    self.update(set__progress=progress)
            except Exception, e:
                log.error(u"Task %s failed: %s" % (self.id, e))
                self.fail_task()
            else:
                self.unlock_task()
                self.status = TaskStatus.successful
                self.save()

    @classmethod
    def random_uuid(cls):
        return str(uuid.uuid4())

    @classmethod
    def pop(cls, queues):
        task_id = cls.random_uuid()
        cls.objects(queue__in=queues, status=TaskStatus.pending).update_one(
            set__locked_by=task_id, set__locked_since=datetime.datetime.now())
        return cls.objects(locked_by=task_id).first()

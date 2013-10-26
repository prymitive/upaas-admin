# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

import os
import datetime
import logging
from socket import gethostname

from mongoengine import (StringField, DateTimeField, IntField, ListField,
                         BooleanField, ReferenceField, Document)

from django.utils.translation import ugettext_lazy as _

from upaas.processes import is_pid_running

from upaas_admin.apps.tasks.constants import (
    STATUS_CHOICES, ACTIVE_TASK_STATUSES, TaskStatus)
from upaas_admin.apps.tasks.registry import find_task_class


log = logging.getLogger(__name__)


class Task(Document):
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    date_finished = DateTimeField()
    title = StringField(required=True)
    status = StringField(required=True, choices=STATUS_CHOICES,
                         default=TaskStatus.pending)
    progress = IntField(min_value=0, max_value=100, default=0)
    messages = ListField(StringField())

    # virtual tasks are used to aggregate progress of group of tasks
    # for example: starting application on multiple backends
    is_virtual = BooleanField(default=False)
    parent = ReferenceField('VirtualTask', dbref=False)
    parent_started = BooleanField(default=False)

    locked_since = DateTimeField()
    locked_by_backend = StringField()
    locked_by_pid = IntField()

    worker_hostname = gethostname()
    worker_pid = os.getpid()

    meta = {
        'abstract': True,
        'ordering': ['-locked_since', '-date_finished', '-date_created'],
        'indexes': ['id', 'is_virtual', 'parent', 'parent_started', 'status',
                    'date_created', 'locked_since', 'locked_by_backend',
                    'locked_by_pid'],
    }

    @property
    def safe_id(self):
        return str(self.id)

    def unlock_task(self):
        """
        Set all attributes needed when unlocking locked task. Unlocking happens
        when worker finishes running task or it has failed.
        """
        self.reload()
        self.date_finished = datetime.datetime.now()
        del self.locked_by_backend
        del self.locked_by_pid
        del self.locked_since

    def fail_task(self):
        """
        Mark task as failed and unlock it.
        """
        self.unlock_task()
        self.status = TaskStatus.failed
        self.save()

    def execute(self):
        """
        Task execution happens here, this is base method that executes task job
        code implemented in job() method.
        """
        if self.parent:
            # mark all subtask as part of started parent
            self.__class__.objects(parent=self.parent).update(
                set__parent_started=True)
            # mark parent as started
            self.parent.__class__.objects(id=self.parent.id).update_one(
                set__locked_since=datetime.datetime.now(),
                set__status=TaskStatus.running)
        try:
            for progress in self.job():
                if progress is not None:
                    log.info(u"Task progress: %d%%" % progress)
                    self.update(set__progress=progress)
        except Exception, e:
            log.error(u"Task %s failed: %s" % (self.id, e))
            self.fail_task()
        else:
            self.unlock_task()
            self.status = TaskStatus.successful
            self.save()

        if not self.parent:
            self.cleanup()

        # if there are no more unfinished task for our parent we mark it as
        # finished
        if self.parent and not self.__class__.objects(
                parent=self.parent, status__in=ACTIVE_TASK_STATUSES):
            self.cleanup()
            statuses = self.__class__.objects(parent=self.parent).distinct(
                'status')
            if TaskStatus.failed in statuses:
                self.parent.__class__.objects(id=self.parent.id).update_one(
                    set__status=TaskStatus.failed)
            else:
                self.parent.__class__.objects(id=self.parent.id).update_one(
                    set__status=TaskStatus.successful)

    def job(self):
        """
        Implement task run code here.
        """
        if not self.is_virtual:
            raise NotImplementedError(_(u"Task has no job defined!"))

    def cleanup(self):
        """
        Executed when task finishes. In case of group of tasks it will be
        executed by last virtual task subtask, once it has finished executing
        its job. If task is parentless it will call cleanup by itself.
        """
        pass

    @classmethod
    def find(cls, task_class, **kwargs):
        """
        Returns list of created tasks of given class with given filter.
        """
        ret = []
        klass = find_task_class(task_class)
        if klass:
            ret = klass.objects(**kwargs)
        return ret

    @classmethod
    def put(cls, task_class, *args, **kwargs):
        """
        Create new task with given arguments and place in on the queue.
        Returns task instance.
        """
        klass = find_task_class(task_class)
        if klass:
            task = klass(*args, **kwargs)
            task.save()
            return task
        else:
            raise ValueError("Task class '%s' not registered!" % task_class)

    @classmethod
    def pop(cls, with_parent=False, **kwargs):
        """
        Pop one pending task from the queue. Returns task instance or None
        if there is no pending task.
        First we try to get tasks with parent task already started, if no such
        task is found we do second query for any task.
        """
        if with_parent:
            # first query gets extra filter
            kwargs['parent_started'] = True
        else:
            # do first query
            task = cls.pop(with_parent=True, **kwargs)
            if task:
                return task
            # if first query didn't return anything we pass to normal query

        cls.objects(status=TaskStatus.pending, is_virtual=False,
                    **kwargs).update_one(
            set__locked_by_backend=cls.worker_hostname,
            set__locked_by_pid=cls.worker_pid,
            set__locked_since=datetime.datetime.now(),
            set__status=TaskStatus.running)
        return cls.objects(locked_by_backend=cls.worker_hostname,
                           locked_by_pid=cls.worker_pid).first()

    @classmethod
    def cleanup_local_tasks(cls):
        """
        Cleanup all interrupted tasks assigned to local backend and mark them
        as failed.
        """
        # look for tasks locked at least 60 seconds ago
        timestamp = datetime.datetime.now() - datetime.timedelta(seconds=60)
        for task in cls.objects(locked_by_backend=cls.worker_hostname,
                                locked_by_pid__ne=cls.worker_pid,
                                locked_since__lte=timestamp):
            if not is_pid_running(task.locked_by_pid):
                log.warning(u"Task '%s' with id %s is locked by non existing "
                            u"pid %d, marking as failed" % (
                                task.__class__.__name__,
                                task.safe_id, task.locked_by_pid))
                task.fail_task()

    @classmethod
    def cleanup_remote_tasks(cls):
        """
        Cleanup all interrupted tasks assigned to remote backends and mark them
        as failed.
        """
        # look for backends that did not ack itself to the database
        pass
        #TODO add backend acking task class to db every few seconds
        # look for task classes that are not acked and fail all tasks

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
                         BooleanField, ReferenceField, Document,
                         EmbeddedDocument, EmbeddedDocumentField)

from django.utils.translation import ugettext_lazy as _

from upaas.processes import is_pid_running

from upaas_admin.apps.tasks.constants import *
from upaas_admin.apps.tasks.registry import find_task_class


log = logging.getLogger(__name__)


class MongoLogHandler(logging.StreamHandler):

    def __init__(self, task, flush_count=10, flush_time=3, *args,
                 **kwargs):
        super(MongoLogHandler, self).__init__(*args, **kwargs)

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
        msg = TaskMessage(
            timestamp=datetime.datetime.fromtimestamp(record.created),
            source=record.name, level=record.levelno, message=record.msg)
        self.messages.append(msg)
        if len(self.messages) >= self.flush_count:
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
    title = StringField(required=True)
    status = StringField(required=True, choices=STATUS_CHOICES,
                         default=TaskStatus.pending)
    progress = IntField(min_value=0, max_value=100, default=0)

    messages = ListField(EmbeddedDocumentField(TaskMessage))

    #TODO tasks should expire, we don;t want start task for backend hanging
    # forever

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

    #TODO add retry support
    retries = IntField()

    can_retry = False
    max_retries = 2

    log_handler = None

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

    @property
    def icon_class(self):
        if self.is_pending:
            return ICON_PENDING
        elif self.is_running:
            return ICON_STARTED
        elif self.is_failed:
            return ICON_FAILED
        elif self.is_successful:
            return ICON_SUCCESSFUL
        return ICON_UNKNOWN

    @property
    def is_pending(self):
        return self.status == TaskStatus.pending

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
    def is_active(self):
        return self.status in ACTIVE_TASK_STATUSES

    @property
    def is_finished(self):
        return self.status in FINISHED_TASKS_STATUSES

    def unlock_task(self):
        """
        Set all attributes needed when unlocking locked task. Unlocking happens
        when worker finishes running task or it has failed.
        """
        if self.log_handler:
            self.remove_logger()
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

    def add_logger(self):
        """
        Add log handler that will store all logs in mongo.
        """
        self.log_handler = MongoLogHandler(self)
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)

    def remove_logger(self):
        """
        Remove mongo log handler.
        """
        self.log_handler.flush()
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.log_handler)

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

        self.add_logger()
        try:
            for progress in self.job():
                if progress is not None:
                    log.debug(u"Task progress: %d%%" % progress)
                    self.update(set__progress=progress)
        except Exception, e:
            log.error(u"Task %s failed: %s" % (self.id, e))
            self.fail_task()
        else:
            self.unlock_task()
            self.status = TaskStatus.successful
            self.save()

        if not self.parent:
            log.info(u"Stand alone task, calling cleanup")
            self.cleanup()

        # if there are no more unfinished task for our parent we mark it as
        # finished
        # search is done on base class to catch all inherited classes
        if self.parent and not self.__class__.__base__.objects(
                parent=self.parent, status__in=ACTIVE_TASK_STATUSES):
            log.info(u"Last task in group, calling cleanup")
            self.cleanup()
            statuses = self.__class__.__base__.objects(
                parent=self.parent).distinct('status')
            if TaskStatus.failed in statuses:
                log.info(u"Marking parent (%s) as failed, subtasks distinct "
                         u"statuses: %s" % (self.parent.safe_id, statuses))
                self.parent.__class__.objects(id=self.parent.id).update_one(
                    set__status=TaskStatus.failed)
            else:
                log.info(u"Marking parent (%s) as successful, subtasks "
                         u"distinct statuses: %s" % (self.parent.safe_id,
                                                     statuses))
                self.parent.__class__.objects(id=self.parent.id).update_one(
                    set__status=TaskStatus.successful)
            # remove parent_started mark on all subtask
            self.__class__.objects(parent=self.parent).update(
                set__parent_started=False)

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

    def generate_title(self):
        """
        Task classes can implement this method to generate task title,
        generated title will be used when user did not provided it.
        """
        return _(u"Unnamed task")

    @property
    def subtasks(self):
        """
        Returns list of sub tasks if current task is virtual or empty list.
        """
        return self.__class__.objects(parent=self.id)

    @classmethod
    def find(cls, task_class, **kwargs):
        """
        Returns list of created tasks of given class with given filter.
        """
        ret = []
        klass = find_task_class(task_class)
        if klass:
            ret = klass.objects(**kwargs)
        else:
            log.error(u"Task class not found: %s" % task_class)
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
            if not task.title:
                task.title = task.generate_title()
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

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from mongoengine import ReferenceField

from upaas_admin.apps.tasks.models import Task
from upaas_admin.common.logger import MongoLogHandler


class VirtualTask(Task):
    """
    Task group, doesn't do anything, only tracks progress of subtasks.
    All tasks in the group must have the same class.
    """

    meta = {
        'collection': 'tasks',
    }


class BackendTask(Task):
    """
    Generic task that will run on specific backend server.
    """

    backend = ReferenceField('BackendServer', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
        'indexes': ['backend'],
        'collection': 'tasks',
    }


class ApplicationTask(Task):
    """
    Task that will run on any backend server for specific application.
    """

    application = ReferenceField('Application', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
        'indexes': ['application'],
        'collection': 'tasks',
    }

    def before_execute(self):
        self.log_handler = MongoLogHandler(self)
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)

    def after_execute(self):
        self.log_handler.flush()
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.log_handler)


class PackageTask(BackendTask, ApplicationTask):
    """
    Task that will run on specific backend server for specific application.
    """

    package = ReferenceField('Package', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
        'indexes': ['application', 'backend'],
    }

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import ReferenceField

from upaas_admin.apps.tasks.models import Task


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


class PackageTask(BackendTask, ApplicationTask):
    """
    Task that will run on specific backend server for specific application.
    """

    package = ReferenceField('Package', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
        'indexes': ['application', 'backend'],
    }

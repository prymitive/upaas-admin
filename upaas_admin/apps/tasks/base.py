# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import ReferenceField

from upaas_admin.apps.tasks.models import Task


class BackendTask(Task):
    """
    Task that will run on specific backend server.
    """

    backend = ReferenceField('BackendServer', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
    }


class ApplicationTask(Task):
    """
    Task that will run on any backend server for specific application.
    """

    application = ReferenceField('Application', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
    }


class PackageTask(Task):
    """
    Task that will run on specific backend server for specific application.
    """

    backend = ReferenceField('BackendServer', dbref=False, required=True)
    application = ReferenceField('Application', dbref=False, required=True)
    package = ReferenceField('Package', dbref=False, required=True)

    meta = {
        'allow_inheritance': True,
    }

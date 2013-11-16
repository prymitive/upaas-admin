# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from datetime import datetime, timedelta
from time import sleep
import logging

from mongoengine import ReferenceField

from django.utils.translation import ugettext_lazy as _

from upaas_admin.apps.tasks.models import Task
from upaas_admin.apps.servers.constants import PortsNames
from upaas_admin.common.uwsgi import fetch_json_stats


log = logging.getLogger(__name__)


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


class PackageTask(BackendTask, ApplicationTask):
    """
    Task that will run on specific backend server for specific application.
    """

    package = ReferenceField('Package', dbref=False, required=True)

    # time limit for graceful operations, how long should we wait for app to
    # start before giving up
    graceful_timeout = 300

    meta = {
        'allow_inheritance': True,
        'indexes': ['application', 'backend'],
    }

    def wait_until_running(self, timelimit=None):
        if timelimit is None:
            timelimit = self.graceful_timeout

        ports_data = self.backend.application_ports(self.application)
        if ports_data and ports_data.ports.get(PortsNames.stats):
            ip = str(self.backend.ip)
            name = self.application.name
            #FIXME track pid change instead of initial sleep (?)
            sleep(3)
            timeout = datetime.now() + timedelta(seconds=timelimit)
            logged = False
            while datetime.now() <= timeout:
                s = fetch_json_stats(ip, ports_data.ports[PortsNames.stats])
                if s:
                    return True
                if logged:
                    log.debug(_(u"Waiting for {name} to start").format(
                        name=name))
                else:
                    log.info(_(u"Waiting for {name} to start").format(
                        name=name))
                    logged = True
                sleep(2)
            else:
                log.error(_(u"Timeout reached but {name} doesn't appear to be "
                            u"running yet").format(name=name))

        return False

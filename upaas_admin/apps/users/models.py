# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import hmac
import uuid
import hashlib
import logging
from datetime import datetime, timedelta

from mongoengine.queryset import QuerySetManager
from mongoengine.django.auth import User as MongoUser
from mongoengine.fields import StringField
from mongoengine import signals, Q

from upaas_admin.apps.scheduler.models import UserLimits, ApplicationRunPlan
from upaas_admin.apps.applications.models import Application, TaskDetails
from upaas_admin.apps.tasks.constants import ACTIVE_TASK_STATUSES


log = logging.getLogger(__name__)


class User(MongoUser):

    apikey = StringField(required=True)

    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    _default_manager = QuerySetManager()

    meta = {
        'allow_inheritance': True,
        'indexes': [
            {'fields': ['username', 'apikey'], 'unique': True},
            {'fields': ['is_active']},
        ]
    }

    @classmethod
    def generate_apikey(cls):
        apikey = None
        while apikey is None and User.objects(apikey=apikey) not in [None, []]:
            log.debug("Trying to generate unique API key")
            apikey = hmac.new(uuid.uuid4().bytes,
                              digestmod=hashlib.sha1).hexdigest()
        return apikey

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.apikey:
            log.info("Generating API key for '%s'" % document.username)
            document.apikey = User.generate_apikey()

    @property
    def safe_id(self):
        return str(self.id)

    @property
    def full_name_or_login(self):
        return self.get_full_name() or self.username

    @property
    def limits_settings(self):
        return UserLimits.objects(user=self).first()

    @property
    def limits(self):
        ret = UserLimits.get_default_limits()
        user_limits = self.limits_settings
        if user_limits:
            for name in UserLimits.limit_fields:
                value = getattr(user_limits, name)
                if value is not None:
                    ret[name] = value
        return ret

    @property
    def limits_usage(self):
        ret = {'running_apps': 0, 'workers': 0}
        for arp in ApplicationRunPlan.objects(
                application__in=Application.objects(owner=self)):
            ret['running_apps'] += 1
            ret['workers'] += arp.workers_max
        return ret

    @property
    def applications(self):
        return Application.objects(owner=self)

    @property
    def running_applications(self):
        return [arp.application for arp in ApplicationRunPlan.objects(
            application__in=Application.objects(owner=self))]

    @property
    def tasks(self):
        """
        List of all tasks for this application.
        """
        return TaskDetails.objects(application__in=self.applications)

    @property
    def recent_tasks(self):
        return self.tasks.filter(
            Q(status__in=ACTIVE_TASK_STATUSES) |
            Q(date_finished__gte=datetime.now() - timedelta(seconds=3600)))

    @staticmethod
    def has_usable_password():
        return True

signals.pre_save.connect(User.pre_save, sender=User)

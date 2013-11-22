# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import hmac
import uuid
import hashlib
import logging

from mongoengine.queryset import QuerySetManager
from mongoengine.django.auth import User as MongoUser
from mongoengine.fields import StringField
from mongoengine import signals

from upaas_admin.apps.scheduler.models import UserLimits, ApplicationRunPlan
from upaas_admin.apps.applications.models import Application


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
            apikey = hmac.new(
                str(uuid.uuid4()), digestmod=hashlib.sha1).hexdigest()
        return apikey

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.apikey:
            log.info("Generating API key for '%s'" % document.username)
            document.apikey = User.generate_apikey()

    @property
    def full_name_or_login(self):
        return self.get_full_name() or self.username

    @property
    def limits(self):
        default_limits = UserLimits.get_default_limits()
        user_limits = UserLimits.objects(user=self).first()
        if user_limits:
            ret = {}
            for name in UserLimits.limit_fields:
                value = getattr(user_limits, name)
                if value is not None:
                    ret[name] = value
                else:
                    ret[name] = default_limits[name]
            return ret
        return default_limits

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


signals.pre_save.connect(User.pre_save, sender=User)

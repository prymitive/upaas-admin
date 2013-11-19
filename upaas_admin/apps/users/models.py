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

from upaas_admin.apps.scheduler.models import UserBudget, ApplicationRunPlan
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
    def post_init(cls, sender, document, **kwargs):
        if document.id:
            if document.budget:
                document.sync_budget()
            else:
                document.create_default_budget()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.apikey:
            log.info("Generating API key for '%s'" % document.username)
            document.apikey = User.generate_apikey()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if not document.budget:
            document.create_default_budget()

    @property
    def full_name_or_login(self):
        return self.get_full_name() or self.username

    @property
    def budget(self):
        return UserBudget.objects(user=self).first()

    @property
    def applications(self):
        return Application.objects(owner=self)

    @property
    def running_applications(self):
        return [arp.application for arp in ApplicationRunPlan.objects(
            application__in=Application.objects(owner=self))]

    @property
    def limits_usage(self):
        usage = {'instance_limit': 0, 'worker_limit': 0, 'memory_limit': 0}
        for arp in ApplicationRunPlan.objects(
                application__in=Application.objects(owner=self)):
            usage['instance_limit'] += len(arp.backends)
            usage['worker_limit'] += arp.worker_limit
            usage['memory_limit'] += arp.memory_limit
        return usage

    def create_default_budget(self):
        log.info(u"Saving default user budget for '%s'" % self.username)
        user_budget = UserBudget(user=self, **UserBudget.get_default_limits())
        user_budget.save()

    def sync_budget(self):
        #TODO move to admin command (?)
        changed = False
        budget = self.budget
        for key, value in UserBudget.get_default_limits().items():
            if getattr(budget, key) is None:
                log.info(u"Updating user '%s' budget with defaults: %s => "
                         u"%s" % (self.username, key, value))
                setattr(budget, key, value)
                changed = True
        if changed:
            budget.save()


signals.post_init.connect(User.post_init, sender=User)
signals.pre_save.connect(User.pre_save, sender=User)
signals.post_save.connect(User.post_save, sender=User)

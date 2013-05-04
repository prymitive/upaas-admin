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


log = logging.getLogger(__name__)


class User(MongoUser):

    _default_manager = QuerySetManager()

    apikey = StringField(required=True)

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

    meta = {
        'allow_inheritance': True,
        'indexes': [
            {'fields': ['username', 'apikey'], 'unique': True}
        ]
    }


signals.pre_save.connect(User.pre_save, sender=User)

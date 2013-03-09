# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import hmac
import uuid
import hashlib

from mongoengine.queryset import QuerySetManager
from mongoengine.django.auth import User as MongoUser
from mongoengine.fields import StringField
from mongoengine import signals


class User(MongoUser):

    _default_manager = QuerySetManager()

    apikey = StringField(required=True)

    @classmethod
    def generate_apikey(cls):
        return hmac.new(str(uuid.uuid4()), digestmod=hashlib.sha1).hexdigest()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.apikey:
            document.apikey = User.generate_apikey()


signals.pre_save.connect(User.pre_save, sender=User)

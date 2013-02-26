# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)


SESSION_ENGINE = 'mongoengine.django.sessions'

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from upaas_admin.contrib.fields import IPField


class BackendServer(Document):
    """
    Backend server - used for running applications.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, help_text=_('Backend name'))
    enabled = BooleanField(default=True, help_text=_('Enabled'))
    ip = IPField(required=True, unique=True, help_text=_('Backend IP address'))


class RouterServer(Document):
    """
    Router server - used for load balancing.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    enabled = BooleanField(default=True, help_text=_('Enabled'))
    name = StringField(required=True, help_text=_('Router name'))
    private_ip = IPField(required=True, unique=True,
                         help_text=_('IP address for private services'))
    public_ip = IPField(required=True, unique=True,
                        help_text=_('IP address for public services'))

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import *

from django.utils.translation import ugettext_lazy as _


class UserBudget(Document):
    """
    How much resources can user apps consume.
    """
    memory_limit = LongField(required=True, verbose_name=_('memory limit'))
    cpu_shares = LongField(required=True, verbose_name=_('cpu shares'))

    _default_manager = QuerySetManager()

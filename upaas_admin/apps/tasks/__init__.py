# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from registry import tasks_autodiscover


log = logging.getLogger(__name__)


try:
    tasks_autodiscover()
except:
    log.debug(u"Task discovery failed")

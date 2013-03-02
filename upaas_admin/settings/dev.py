# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas_admin.settings.base import *   # pylint: disable=W0614,W0401


DEBUG = True
TEMPLATE_DEBUG = DEBUG

VAR_ROOT = '/var/www/upaas_admin'
MEDIA_ROOT = os.path.join(VAR_ROOT, 'uploads')
STATIC_ROOT = os.path.join(VAR_ROOT, 'static')

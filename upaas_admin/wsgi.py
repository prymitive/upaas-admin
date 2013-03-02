# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "upaas_admin.settings.local")


from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

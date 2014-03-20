# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas_admin.settings.tests import *

from IPy import IP


DEBUG = True
TEMPLATE_DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


#==============================================================================
# django-debug-toolbar
#==============================================================================

INSTALLED_APPS += (
    'debug_toolbar',
    'template_timings_panel',
    'debug_toolbar_mongo',
)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

# code from http://djangosnippets.org/snippets/1362/


class IPList(list):

    def __init__(self, ips):
        try:
            for ip in ips:
                self.append(IP(ip))
        except ImportError:
            pass

    def __contains__(self, ip):
        try:
            for net in self:
                if ip in net:
                    return True
        except:
            pass
        return False

INTERNAL_IPS = IPList(['127.0.0.1', '10.0.0.0/8', '172.16.0.0/12',
                      '192.168.0.0/16'])

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    'debug_toolbar_mongo.panel.MongoDebugPanel',
    #'debug_toolbar.panels.logging.LoggingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'RENDER_PANELS': True,
}

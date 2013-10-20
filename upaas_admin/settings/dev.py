# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas_admin.settings.prod import *


from IPy import IP


TEMPLATE_LOADERS = (
    'hamlpy.template.loaders.HamlPyFilesystemLoader',
    'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)


LOGGING = ['handlers']['console']['level'] = 'DEBUG'


#==============================================================================
# django-pipeline
#==============================================================================

PIPELINE_ENABLED = False

STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'


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
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    #'debug_toolbar.panels.logger.LoggingPanel',
    'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar_mongo.panel.MongoDebugPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

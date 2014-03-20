# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas_admin.settings.prod import *


TEMPLATE_LOADERS = (
    'hamlpy.template.loaders.HamlPyFilesystemLoader',
    'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)


LOGGING['handlers']['console']['level'] = 'DEBUG'


#==============================================================================
# django-pipeline
#==============================================================================

PIPELINE_ENABLED = False

STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'

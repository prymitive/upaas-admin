# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.global_settings import *   # pylint: disable=W0614,W0401


#==============================================================================
# Generic Django project settings
#==============================================================================

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SITE_ID = 1
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'UTC'
USE_TZ = True
USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', 'English'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'hf(i1^w^c@cc@err0m5ho$oc&@yxsywsvlgc&co+%!9+o_56pn'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pipeline',
    'crispy_forms',
    'django_bootstrap_breadcrumbs',
    'tastypie',
    'tastypie_mongoengine',
    'upaas_admin.apps.users',
)


#==============================================================================
# Calculation of directories relative to the project module location
#==============================================================================

import os
import upaas_admin as project_module

PROJECT_DIR = os.path.dirname(os.path.realpath(project_module.__file__))

VAR_ROOT = os.path.join(PROJECT_DIR, 'var')

if not os.path.exists(VAR_ROOT):
    os.mkdir(VAR_ROOT)


#==============================================================================
# Project URLS and media settings
#==============================================================================

ROOT_URLCONF = 'upaas_admin.urls'

LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/'

STATIC_URL = '/static/'
MEDIA_URL = '/uploads/'

STATIC_ROOT = os.path.join(VAR_ROOT, 'static')
MEDIA_ROOT = os.path.join(VAR_ROOT, 'uploads')

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)


#==============================================================================
# Templates
#==============================================================================

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)

#TODO cached loader?
TEMPLATE_LOADERS = (
    'hamlpy.template.loaders.HamlPyFilesystemLoader',
    'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)


#==============================================================================
# Middleware
#==============================================================================

MIDDLEWARE_CLASSES += (
)


#==============================================================================
# Auth / security
#==============================================================================

#AUTHENTICATION_BACKENDS += (
#)
LOGIN_URL = '/login'
LOGOUT_URL = '/logout'
LOGIN_REDIRECT_URL = '/'

#==============================================================================
# MongoEngine
#==============================================================================

from mongoengine import connect

MONGODB_DATABASE = 'upaas'

AUTHENTICATION_BACKENDS = ('mongoengine.django.auth.MongoEngineBackend',)

SESSION_ENGINE = 'mongoengine.django.sessions'

connect(MONGODB_DATABASE)


#==============================================================================
# django-pipeline
#==============================================================================

STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'bootstrap/css/bootstrap.css',
        ),
        'output_filename': 'css/bootstrap.css',
    }
}

PIPELINE_JS = {
    'base': {
        'source_filenames': (
            'jquery/jquery-1.9.1.js',
            'bootstrap/js/bootstrap.js',
        ),
        'output_filename': 'js/base.js',
        }
}


PIPELINE_JS = {
    'html5shiv': {
        'source_filenames': (
            'bootstrap/js/html5shiv.js',
        ),
        'output_filename': 'js/html5shiv.js',
        }
}

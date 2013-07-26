# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import sys
import logging

from tzlocal import get_localzone

from upaas.config.main import load_main_config

from django.conf.global_settings import *   # pylint: disable=W0614,W0401


# basic logger needed to print startup errors
logging.basicConfig()


#==============================================================================
# Generic Django project settings
#==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}

DEBUG = False
TEMPLATE_DEBUG = False

SITE_ID = 1

# set local time zone
TIME_ZONE = get_localzone().zone
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
    'mongoengine.django.mongo_auth',
    'dajaxice',
    'pipeline',
    'crispy_forms',
    'django_bootstrap_breadcrumbs',
    'tastypie',
    'tastypie_mongoengine',
    'pure_pagination',
    'djcelery',
    'django_gravatar',
    'upaas_admin.apps.users',
    'upaas_admin.apps.applications',
    'upaas_admin.apps.servers',
)


#==============================================================================
# Calculation of directories relative to the project module location
#==============================================================================

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
# Static files
#==============================================================================

STATICFILES_FINDERS += (
    'dajaxice.finders.DajaxiceFinder',
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
    'django.template.loaders.eggs.Loader',
)


#==============================================================================
# Middleware
#==============================================================================

MIDDLEWARE_CLASSES += (
    'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
)


#==============================================================================
# Auth / security
#==============================================================================

AUTH_USER_MODEL = 'mongo_auth.MongoUser'

LOGIN_URL = '/login'
LOGOUT_URL = '/logout'
LOGIN_REDIRECT_URL = '/'

#==============================================================================
# MongoEngine
#==============================================================================

SESSION_ENGINE = 'mongoengine.django.sessions'

MONGOENGINE_USER_DOCUMENT = 'upaas_admin.apps.users.models.User'

upaas_config = load_main_config()

if not upaas_config:
    sys.exit(1)

from mongoengine import connect
mongo_opts = dict(host=upaas_config.mongodb.host,
                  port=upaas_config.mongodb.port)
if upaas_config.mongodb.get('username'):
    mongo_opts['username'] = upaas_config.mongodb.username
    if upaas_config.mongodb.get('password'):
        mongo_opts['password'] = upaas_config.mongodb.password

connect(upaas_config.mongodb.database, **mongo_opts)

#==============================================================================
# celery
#==============================================================================

import djcelery
djcelery.setup_loader()

mongouri = "mongodb://"

if upaas_config.mongodb.get('username'):
    mongouri += upaas_config.mongodb.username
    if upaas_config.mongodb.get('password'):
        mongouri += ':' + upaas_config.mongodb.password
    mongouri += "@"

mongouri += "%s:%s/%s" % (upaas_config.mongodb.host,
                          upaas_config.mongodb.port,
                          upaas_config.mongodb.database)

BROKER_URL = mongouri

CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": upaas_config.mongodb.host,
    "port": upaas_config.mongodb.port,
    "database": upaas_config.mongodb.database,
}

if upaas_config.mongodb.get('username'):
    CELERY_MONGODB_BACKEND_SETTINGS['user'] = upaas_config.mongodb.username
    if upaas_config.mongodb.get('password'):
        CELERY_MONGODB_BACKEND_SETTINGS['password'] = upaas_config.\
            mongodb.password

CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = CELERY_MONGODB_BACKEND_SETTINGS
CELERY_TRACK_STARTED = True

#==============================================================================
# django-pipeline
#==============================================================================

STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'

PIPELINE_COMPILERS = (
    'pipeline.compilers.less.LessCompiler',
)

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'bootstrap/less/bootstrap.less',
            'upaas/site.less',
        ),
        'output_filename': 'css/bootstrap.css',
    },
    'zeroclipboard': {
        'source_filenames': (
            'zeroclipboard/zeroclipboard.less',
        ),
        'output_filename': 'css/zeroclipboard.css',
    },
}

PIPELINE_JS = {
    'base': {
        'source_filenames': (
            'jquery/jquery-1.10.1.js',
            'bootstrap/js/bootstrap.js',
            'upaas/csrf.js',
        ),
        'output_filename': 'js/base.js',
    },
    'html5shiv': {
        'source_filenames': (
            'bootstrap/js/html5shiv.js',
        ),
        'output_filename': 'js/html5shiv.js',
    },
    'zeroclipboard': {
        'source_filenames': (
            'zeroclipboard/ZeroClipboard.js',
        ),
        'output_filename': 'js/zeroclipboard.js',
    },
}


#==============================================================================
# logging
#==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] "
                      "%(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'tastypie': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'tastypie_mongoengine': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

#==============================================================================
# gravatar
#==============================================================================

GRAVATAR_DEFAULT_IMAGE = 'wavatar'


#==============================================================================
# django-pure-pagination
#==============================================================================

PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 6,
    'MARGIN_PAGES_DISPLAYED': 2,
}

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import sys
import logging

from tzlocal import get_localzone

from upaas_admin.config import load_main_config

from django.conf.global_settings import *   # pylint: disable=W0614,W0401


# basic logger needed to print startup errors
log = logging.basicConfig()


# =============================================================================
# UPaaS configuraton file
# =============================================================================
UPAAS_CONFIG = load_main_config()

if not UPAAS_CONFIG:
    print("Missing or invalid configuration file!")
    sys.exit(1)


# =============================================================================
# Generic Django project settings
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

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

SECRET_KEY = UPAAS_CONFIG.admin.secretkey

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mongoengine.django.mongo_auth',
    'djangojs',
    'dajaxice',
    'pipeline',
    'crispy_forms',
    'django_bootstrap_breadcrumbs',
    'tastypie',
    'tastypie_mongoengine',
    'pure_pagination',
    'django_gravatar',
    'passwords',
    'upaas_admin.apps.users',
    'upaas_admin.apps.applications',
    'upaas_admin.apps.servers',
    'upaas_admin.apps.admin',
    'upaas_admin.apps.tasks',
    'upaas_admin.apps.scheduler',
)


# =============================================================================
# Calculation of directories relative to the project module location
# =============================================================================

import upaas_admin as project_module

PROJECT_DIR = os.path.dirname(os.path.realpath(project_module.__file__))

VAR_ROOT = os.path.join(PROJECT_DIR, 'var')

if not os.path.exists(VAR_ROOT):
    os.mkdir(VAR_ROOT)


# =============================================================================
# Project URLS and media settings
# =============================================================================

ROOT_URLCONF = 'upaas_admin.urls'

STATIC_URL = '/static/'
MEDIA_URL = '/uploads/'

STATIC_ROOT = os.path.join(VAR_ROOT, 'static')
MEDIA_ROOT = os.path.join(VAR_ROOT, 'uploads')

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)


# =============================================================================
# Static files
# =============================================================================

STATICFILES_FINDERS += (
    'dajaxice.finders.DajaxiceFinder',
)


# =============================================================================
# Templates
# =============================================================================

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'hamlpy.template.loaders.HamlPyFilesystemLoader',
        'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader'),),
)


# =============================================================================
# Middleware
# =============================================================================

MIDDLEWARE_CLASSES += (
)


# =============================================================================
# Auth / security
# =============================================================================

AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)

AUTH_USER_MODEL = 'mongo_auth.MongoUser'

LOGIN_URL = '/login'
LOGOUT_URL = '/logout'
LOGIN_REDIRECT_URL = '/'

ALLOWED_HOSTS = UPAAS_CONFIG.admin.domains or ['*']

# =============================================================================
# MongoEngine
# =============================================================================

SESSION_ENGINE = 'mongoengine.django.sessions'
SESSION_SERIALIZER = 'mongoengine.django.sessions.BSONSerializer'

MONGOENGINE_USER_DOCUMENT = 'upaas_admin.apps.users.models.User'

from mongoengine import connect
from pymongo import ReadPreference

mongo_opts = {}

if UPAAS_CONFIG.mongodb.get('uri'):
    # URI scheme is used for connecting
    db = UPAAS_CONFIG.mongodb.uri.split('/')[3].split('?')[0]
    connect(db, host=UPAAS_CONFIG.mongodb.uri)
else:
    # host & port settings
    mongo_opts = {'host': UPAAS_CONFIG.mongodb.host,
                  'port': UPAAS_CONFIG.mongodb.port,
                  'read_preference': ReadPreference.PRIMARY_PREFERRED}
    if UPAAS_CONFIG.mongodb.get('username'):
        mongo_opts['username'] = UPAAS_CONFIG.mongodb.username
        if UPAAS_CONFIG.mongodb.get('password'):
            mongo_opts['password'] = UPAAS_CONFIG.mongodb.password

    connect(UPAAS_CONFIG.mongodb.database, **mongo_opts)


# =============================================================================
# django-pipeline
# =============================================================================

# force pipeline to be enabled even if DEBUG=True
PIPELINE_ENABLED = True

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_COMPILERS = (
    'pipeline.compilers.less.LessCompiler',
)

# FIXME disabled js compression for now, fix it and re-enable!
PIPELINE_JS_COMPRESSOR = None

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'bootstrap/less/bootstrap.less',
            'font-awesome/less/font-awesome.less',
            'bootstrap/less/theme.less',
            'tabdrop/tabdrop.less',
            'upaas/less/base/*.less',
        ),
        'output_filename': 'css/bootstrap.css',
    },
    'zeroclipboard': {
        'source_filenames': (
            'zeroclipboard/zeroclipboard.less',
        ),
        'output_filename': 'css/zeroclipboard.css',
    },
    'daterangepicker': {
        'source_filenames': (
            'daterangepicker/daterangepicker.less',
        ),
        'output_filename': 'css/daterangepicker.css',
    },
}

PIPELINE_JS = {
    'base': {
        'source_filenames': (
            'jquery/jquery-2.0.3.min.js',
            'bootstrap/js/bootstrap.min.js',
            'js/djangojs/django.min.js',
            'moment-js/moment-with-langs.min.js',
            'underscore/underscore-min.js',
            'underscore/underscore.string.min.js',
            'haml/haml.min.js',
            'tabdrop/bootstrap-tabdrop.js',
            'backbone/backbone-min.js',
            'backbone/backbone-tastypie.js',
            'upaas/js/base/*.js',
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
            'zeroclipboard/ZeroClipboard.min.js',
        ),
        'output_filename': 'js/zeroclipboard.js',
    },
    'graphite': {
        'source_filenames': (
            'graphite/jquery.graphite.js',
        ),
        'output_filename': 'js/graphite.js',
    },
    'daterangepicker': {
        'source_filenames': (
            'daterangepicker/daterangepicker.js',
        ),
        'output_filename': 'js/daterangepicker.js',
    },

}


# =============================================================================
# logging
# =============================================================================

ADMINS = (('UPAAS Admin', 'root@localhost'),)

loglevel = UPAAS_CONFIG.admin.loglevel.upper()
if not logging.getLevelName(loglevel):
    log.error("Invalid log level name '%s', ignoring" % loglevel)
    loglevel = 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[pid:%(process)s] %(levelname)s: %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': loglevel,
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': loglevel,
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'upaas.config': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# email
# =============================================================================

EMAIL_HOST = UPAAS_CONFIG.admin.smtp.host
EMAIL_PORT = UPAAS_CONFIG.admin.smtp.port
DEFAULT_FROM_EMAIL = UPAAS_CONFIG.admin.smtp.sender

# auth is optional
try:
    EMAIL_HOST_USER = UPAAS_CONFIG.admin.smtp.username
    EMAIL_HOST_PASSWORD = UPAAS_CONFIG.admin.smtp.password
except AttributeError:
    pass

EMAIL_SUBJECT_PREFIX = ''

# =============================================================================
# gravatar
# =============================================================================

GRAVATAR_DEFAULT_IMAGE = 'wavatar'


# =============================================================================
# django-pure-pagination
# =============================================================================

PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 6,
    'MARGIN_PAGES_DISPLAYED': 2,
}


# =============================================================================
# django-crispy-forms
# =============================================================================

CRISPY_TEMPLATE_PACK = 'bootstrap3'


# =============================================================================
# django-passwords
# =============================================================================

PASSWORD_MIN_LENGTH = 8
PASSWORD_COMPLEXITY = {
    "UPPER": 1,
    "LOWER": 1,
    "DIGITS": 1,
    "PUNCTUATION": 0,
    "NON ASCII": 0,
    "WORDS": 1
}

# =============================================================================
# tests
# =============================================================================

TEST_RUNNER = 'upaas_admin.common.tests.MongoEngineTestRunner'


# =============================================================================
# DEBUG
# =============================================================================

if UPAAS_CONFIG.admin.debug:

    logging.warning("Debug mode enabled!")

    DEBUG = UPAAS_CONFIG.admin.debug
    TEMPLATE_DEBUG = DEBUG
    DEBUG_PROPAGATE_EXCEPTIONS = True

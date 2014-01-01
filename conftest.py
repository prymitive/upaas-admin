# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from django.conf import settings
from django.test import Client
from django.test.utils import get_runner

from upaas_admin.apps.users.models import User


def is_configured():
    if settings is None:
        return False
    return settings.configured or os.environ.get('DJANGO_SETTINGS_MODULE')


@pytest.fixture(autouse=True, scope='session')
def _django_runner(request):
    if not is_configured():
        return

    runner_class = get_runner(settings)
    runner = runner_class(interactive=False)

    runner.setup_test_environment()
    request.addfinalizer(runner.teardown_test_environment)

    runner._db_config = runner.setup_databases()

    def db_teardown():
        return runner.teardown_databases(runner._db_config)
    request.addfinalizer(db_teardown)

    return runner


@pytest.fixture(scope="function")
def create_user(request):
    data = {
        'login': 'testlogin',
        'first_name': 'ąćźółęż',
        'last_name': 'CAP1TAL',
        'email': 'email@domain.com',
        'password': '123456789źćż',
    }

    u = User.objects(username=data['login']).first()
    if u:
        u.delete()

    u = User(username=data['login'], first_name=data['first_name'],
             last_name=data['last_name'], email=data['email'],
             is_superuser=False)
    u.set_password(data['password'])
    u.save()

    def cleanup():
        u.delete()
    request.addfinalizer(cleanup)

    request.instance.user = u
    request.instance.user_data = data

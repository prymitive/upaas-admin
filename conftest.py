# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
from socket import gethostname

import pytest
from _pytest.monkeypatch import monkeypatch

from django.conf import settings
from django.test.utils import get_runner
from django.utils.html import escape

from upaas_admin.apps.users.models import User
from upaas_admin.apps.applications.models import Application, Package
from upaas_admin.apps.servers.models import BackendServer, RouterServer
from upaas.distro import distro_name, distro_version, distro_arch


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


@pytest.fixture(scope="function")
def create_superuser(request):
    create_user(request)
    request.instance.user.is_superuser = True
    request.instance.user.save()


@pytest.fixture(scope="function")
def create_app(request):
    data = {
        'name': 'redmine',
        'metadata_path': os.path.join(os.path.dirname(__file__),
                                      'tests/meta/redmine.yml')
    }

    with open(data['metadata_path'], 'rb') as metadata:
        data['metadata'] = metadata.read()

    data['metadata_html'] = escape(data['metadata'])

    app = Application.objects(name=data['name']).first()
    if app:
        app.delete()

    create_user(request)

    app = Application(name=data['name'], owner=request.instance.user,
                      metadata=data['metadata'])
    app.save()

    def cleanup():
        for domain in app.custom_domains:
            domain.delete()
        for pkg in app.packages:
            pkg.delete()
        app.delete()
    request.addfinalizer(cleanup)

    request.instance.app = app
    request.instance.app_data = data


@pytest.fixture(scope="function")
def create_pkg(request):
    create_app(request)

    pkg = Package(metadata=request.instance.app_data['metadata'],
                  application=request.instance.app,
                  interpreter_name=request.instance.app.interpreter_name,
                  interpreter_version=request.instance.app.interpreter_version,
                  filename='pkg', bytes=1024, checksum='abcdefg',
                  builder='fake builder', distro_name=distro_name(),
                  distro_version=distro_version(), distro_arch=distro_arch())
    pkg.save()

    def cleanup():
        pkg.delete()
    request.addfinalizer(cleanup)

    request.instance.app.current_package = pkg
    request.instance.app.save()

    request.instance.pkg = pkg


@pytest.fixture(scope="function")
def create_pkg_list(request):
    create_app(request)

    pkg_list = []

    for i in range(0, 33):
        pkg = Package(
            metadata=request.instance.app_data['metadata'],
            application=request.instance.app,
            interpreter_name=request.instance.app.interpreter_name,
            interpreter_version=request.instance.app.interpreter_version,
            filename='pkg%d' % i, bytes=1024, checksum='abcdefg',
            builder='fake builder', distro_name=distro_name(),
            distro_version=distro_version(), distro_arch=distro_arch())
        pkg.save()
        pkg_list.append(pkg)

    def cleanup():
        for pkg in pkg_list:
            pkg.delete()
    request.addfinalizer(cleanup)

    request.instance.app.current_package = pkg_list[0]
    request.instance.app.save()

    request.instance.pkg_list = pkg_list


@pytest.fixture(scope="function")
def create_backend(request):
    name = gethostname()

    backend = BackendServer.objects(name=name).first()
    if backend:
        backend.delete()

    backend = BackendServer(name=name, ip='127.0.0.1')
    backend.save()

    def cleanup():
        backend.delete()
    request.addfinalizer(cleanup)

    request.instance.backend = backend
    request.instance.backend_name = name


@pytest.fixture(scope="function")
def create_router(request):
    router = RouterServer.objects(name='router').first()
    if router:
        router.delete()

    router = RouterServer(name='router', private_ip='127.0.0.1',
                          public_ip='127.0.0.1')
    router.save()

    def cleanup():
        router.delete()
    request.addfinalizer(cleanup)

    request.instance.router = router


@pytest.fixture(scope="function")
def setup_monkeypatch(request):
    mpatch = monkeypatch()
    request.instance.monkeypatch = mpatch
    request.addfinalizer(mpatch.undo)


@pytest.fixture(scope="function")
def mock_dns_record(request):
    class MockDNSRecord(object):
        def __init__(self, value):
            self.strings = value

    request.instance.mock_dns_record_class = MockDNSRecord

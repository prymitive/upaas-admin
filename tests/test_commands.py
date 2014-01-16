# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.management import call_command
from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase


GETPASS_TRY = 0


class AdminTest(MongoEngineTestCase):

    def test_create_indexes_cmd(self):
        self.assertEqual(call_command('create_indexes'), None)

    @pytest.mark.usefixtures("create_pkg", "create_backend")
    def test_backend_worker_cmd(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan, None)
        self.assertNotEqual(self.app.pending_tasks, [])

        self.assertEqual(
            call_command('backend_worker', task_limit=1), None)

    @pytest.mark.usefixtures("create_app")
    def test_builder_worker_cmd(self):
        # needed so that task class will be registered
        from upaas_admin.apps.applications.tasks import BuildPackageTask
        self.app.build_package()
        self.assertNotEqual(self.app.pending_build_tasks, [])
        self.assertEqual(
            call_command('builder_worker', task_limit=1), None)

    def test_create_user_cmd(self):
        from upaas_admin.apps.users.models import User
        self.assertEqual(call_command('create_user', login='mylogin',
                                      firstname='FirstŁÓŹ',
                                      lastname='ÓŹĆąLast',
                                      email='me@domain.com',
                                      password='12345678'), None)
        u = User.objects(username='mylogin').first()
        self.assertNotEqual(u, None)
        self.assertEqual(u.first_name, 'FirstŁÓŹ')
        self.assertEqual(u.last_name, 'ÓŹĆąLast')
        self.assertEqual(u.email, 'me@domain.com')
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_superuser, False)
        u.delete()

    @pytest.mark.usefixtures("setup_monkeypatch")
    def test_create_user_cmd_password_input(self):
        def _getpass(*args, **kwargs):
            global GETPASS_TRY
            GETPASS_TRY += 1
            if GETPASS_TRY == 2:
                return 'xxx'
            else:
                return '12345678'

        self.monkeypatch.setattr('upaas_admin.apps.users.management.commands.'
                                 'create_user.getpass', _getpass)
        from upaas_admin.apps.users.models import User
        self.assertEqual(call_command('create_user', login='mylogin',
                                      firstname='FirstŁÓŹ',
                                      lastname='ÓŹĆąLast',
                                      email='me@domain.com'), None)
        u = User.objects(username='mylogin').first()
        self.assertNotEqual(u, None)
        self.assertEqual(u.first_name, 'FirstŁÓŹ')
        self.assertEqual(u.last_name, 'ÓŹĆąLast')
        self.assertEqual(u.email, 'me@domain.com')
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_superuser, False)
        u.delete()

    def test_create_user_cmd_missing_options(self):
        from django.core.management.base import CommandError
        with pytest.raises(CommandError):
            self.assertEqual(call_command('create_user'), None)

    def test_create_admin_cmd(self):
        from upaas_admin.apps.users.models import User
        self.assertEqual(call_command('create_user', login='mylogin',
                                      firstname='FirstŁÓŹ',
                                      lastname='ÓŹĆąLast',
                                      email='me@domain.com',
                                      password='12345678',
                                      admin=True), None)
        u = User.objects(username='mylogin').first()
        self.assertNotEqual(u, None)
        self.assertEqual(u.first_name, 'FirstŁÓŹ')
        self.assertEqual(u.last_name, 'ÓŹĆąLast')
        self.assertEqual(u.email, 'me@domain.com')
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_superuser, True)
        u.delete()

    def test_bootstrap_os_image_root_required_cmd(self):
        with pytest.raises(SystemExit):
            self.assertEqual(call_command('bootstrap_os_image', force=True),
                             None)

    def test_bootstrap_os_image_as_user_cmd(self):
        with pytest.raises(OSError):
            self.assertEqual(
                call_command('bootstrap_os_image', as_user=True, force=True),
                None)

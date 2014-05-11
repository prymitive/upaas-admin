# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.management import call_command

from upaas_admin.common.tests import MongoEngineTestCase


GETPASS_TRY = 0


class CommandTest(MongoEngineTestCase):

    def check_task_is_successful(self, task):
        self.assertNotEqual(task, None)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_failed, False)
        self.assertEqual(task.is_successful, True)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.progress, 100)
        self.assertNotEqual(task.date_finished, None)
        self.assertNotEqual(len(task.messages), 0)

    def test_create_indexes_cmd(self):
        self.assertEqual(call_command('create_indexes'), None)

    @pytest.mark.usefixtures("mock_chroot", "mock_build_commands",
                             "create_buildable_app")
    def test_mule_builder_cmd(self):
        self.app.build_package()
        self.assertNotEqual(self.app.flags, [])
        call_command('mule_builder', task_limit=1, ping_disabled=True)

    @pytest.mark.usefixtures("mock_chroot", "mock_build_commands",
                             "create_buildable_app", "create_backend")
    def test_mule_builder_cmd_update_backend(self):
        self.backend.update(set__ip='4.4.4.4', set__cpu_cores=99999,
                            set__memory_mb=1)
        self.backend.reload()
        self.assertEqual(self.backend.ip.strNormal(), '4.4.4.4')
        self.assertEqual(self.backend.cpu_cores, 99999)
        self.assertEqual(self.backend.memory_mb, 1)
        self.app.build_package()
        self.assertNotEqual(self.app.flags, [])
        call_command('mule_builder', task_limit=1, ping_disabled=True)
        self.backend.reload()
        self.assertNotEqual(self.backend.ip.strNormal(), '4.4.4.4')
        self.assertNotEqual(self.backend.cpu_cores, 99999)
        self.assertNotEqual(self.backend.memory_mb, 1)

    @pytest.mark.usefixtures("mock_chroot", "mock_build_commands",
                             "create_buildable_app", "create_backend")
    def test_mule_builder_cmd_pings(self):
        self.assertEqual(self.backend.worker_ping, {})
        self.app.build_package()
        self.assertNotEqual(self.app.flags, [])
        call_command('mule_builder', task_limit=1, ping_interval=1)
        self.backend.reload()
        self.assertNotEqual(self.backend.worker_ping, {})

    @pytest.mark.usefixtures("mock_chroot", "mock_build_commands",
                             "create_buildable_app_with_pkg")
    def test_mule_builder_cmd_incremental(self):
        self.app.build_package()
        self.assertNotEqual(self.app.flags, [])
        call_command('mule_builder', task_limit=1, ping_disabled=True)

    @pytest.mark.usefixtures("mock_chroot", "mock_build_commands",
                             "create_buildable_app")
    def test_mule_builder_cmd_missing_metadata(self):
        self.app.metadata = ''
        self.app.save()
        self.app.build_package()
        self.assertNotEqual(self.app.flags, [])
        call_command('mule_builder', task_limit=1, ping_disabled=True)

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_run_plan")
    def test_mule_backend_cmd_start_missing_pkg_file(self):
        self.app.start_application()
        self.assertNotEqual(len(self.app.flags), 0)
        call_command('mule_backend', task_limit=1, ping_disabled=True)
        task = self.app.tasks.first()
        self.assertNotEqual(task, None)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_failed, True)
        self.assertEqual(task.is_successful, False)
        self.assertEqual(task.is_finished, True)
        self.assertNotEqual(task.date_finished, None)
        self.assertNotEqual(len(task.messages), 0)
        self.assertEqual(task.backend, self.backend)

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_run_plan")
    def test_mule_backend_cmd_start_from_run_plan(self):
        self.app.start_application()
        self.app.flags.delete()
        self.assertEqual(len(self.app.flags), 0)
        call_command('mule_backend', task_limit=1, ping_disabled=True)
        task = self.app.tasks.first()
        self.assertNotEqual(task, None)
        self.assertEqual(task.flag, 'IS_STARTING')

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_run_plan")
    def test_mule_backend_cmd_stop(self):
        self.app.stop_application()
        self.assertNotEqual(len(self.app.flags), 0)
        call_command('mule_backend', task_limit=1, ping_disabled=True)
        self.check_task_is_successful(self.app.tasks.first())

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_run_plan",
                             "setup_monkeypatch")
    def test_mule_backend_cmd_restart(self):
        self.monkeypatch.setattr('upaas_admin.apps.tasks.management.commands.'
                                 'mule_backend.fetch_json_stats',
                                 lambda x, y: True)
        self.app.restart_application()
        self.assertNotEqual(len(self.app.flags), 0)
        call_command('mule_backend', task_limit=1, ping_disabled=True)
        self.check_task_is_successful(self.app.tasks.first())

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

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.applications.tasks import (
    BuildPackageTask, StartApplicationTask, StopApplicationTask,
    UpdateVassalTask)


class TaskTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_app")
    def test_build_package_task_failed(self):
        task = BuildPackageTask(application=self.app,
                                metadata=self.app_data['metadata'])
        task.title = task.generate_title()
        task.save()
        task.execute()
        task.reload()
        self.assertEqual(task.is_successful, False)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, True)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

    @pytest.mark.usefixtures("create_buildable_app", "mock_chroot",
                             "mock_build_commands")
    def test_build_package_task_successful(self):
        task = BuildPackageTask(application=self.app,
                                metadata=self.app_data['metadata'],
                                force_fresh=True)
        task.title = task.generate_title()
        task.save()
        task.execute()

        task.reload()
        self.assertEqual(task.is_successful, True)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, False)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

        self.app.reload()
        self.assertEqual(len(self.app.packages), 1)
        self.assertNotEqual(self.app.current_package, None)
        self.assertNotEqual(self.app.current_package.filename, None)

    @pytest.mark.usefixtures("create_run_plan")
    def test_start_app_task_failed(self):
        self.app.start_application()
        task = StartApplicationTask(application=self.app, backend=self.backend)
        task.title = task.generate_title()
        task.save()
        task.execute()
        task.reload()
        self.assertEqual(task.is_successful, False)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, True)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

    @pytest.mark.usefixtures("create_pkg", "create_backend")
    def test_start_app_task_no_run_plan(self):
        self.app.start_application()
        task = StartApplicationTask(application=self.app, backend=self.backend)
        task.title = task.generate_title()
        task.save()
        task.execute()
        self.assertEqual(task.is_successful, False)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, True)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

    @pytest.mark.usefixtures("create_run_plan")
    def test_stop_app_task_successful(self):
        self.app.start_application()
        task = StopApplicationTask(application=self.app, backend=self.backend)
        task.title = task.generate_title()
        task.save()
        task.execute()
        task.reload()
        self.assertEqual(task.is_successful, True)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, False)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

    @pytest.mark.usefixtures("create_run_plan", "setup_monkeypatch")
    def test_update_app_task_successful(self):
        self.monkeypatch.setattr(
            'upaas_admin.apps.tasks.base.fetch_json_stats',
            lambda x, y: {'stats': False})
        self.app.start_application()
        task = UpdateVassalTask(application=self.app, backend=self.backend)
        task.title = task.generate_title()
        task.save()
        task.execute()
        task.reload()
        self.assertEqual(task.is_successful, True)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, False)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

    @pytest.mark.usefixtures("create_pkg", "create_backend")
    def test_update_app_task_no_run_plan(self):
        self.app.start_application()
        task = UpdateVassalTask(application=self.app, backend=self.backend)
        task.title = task.generate_title()
        task.save()
        task.execute()
        self.assertEqual(task.is_successful, True)
        self.assertEqual(task.is_active, False)
        self.assertEqual(task.is_failed, False)
        self.assertEqual(task.is_finished, True)
        self.assertEqual(task.is_pending, False)
        self.assertEqual(task.is_running, False)
        self.assertEqual(task.is_virtual, False)

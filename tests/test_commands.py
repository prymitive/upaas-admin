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


class AdminTest(MongoEngineTestCase):

    def test_create_indexes_cmd(self):
        self.assertEqual(call_command('create_indexes'), None)

    @pytest.mark.usefixtures("create_pkg")
    @pytest.mark.usefixtures("create_backend")
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
        from upaas_admin.apps.applications.tasks import BuildPackageTask
        self.app.build_package()
        self.assertNotEqual(self.app.pending_build_tasks, [])
        self.assertEqual(
            call_command('builder_worker', task_limit=1), None)

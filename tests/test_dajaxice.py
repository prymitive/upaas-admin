# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import json
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import pytest

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase


class DajaxiceTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_user")
    def test_app_updates_empty_ajax(self):
        self.login_as_user()
        url = '/dajaxice/upaas_admin.apps.applications.apps_updates/'
        resp = self.client.post(url, {},
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotEqual(data, {})
        self.assertNotEqual(data, None)
        self.assertEqual(data['tasks']['running'], 0)
        self.assertEqual(data['tasks']['recent'], 0)
        self.assertEqual(data['tasks']['list'], [])
        self.assertEqual(data['apps']['running'], [])
        self.assertEqual(data['apps']['list'], [])

    @pytest.mark.usefixtures("create_pkg", "create_backend_list")
    def test_app_updates_started_ajax(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 6, 'workers_max': 12})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan, None)

        url = '/dajaxice/upaas_admin.apps.applications.apps_updates/'
        resp = self.client.post(url, {},
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotEqual(data, {})
        self.assertNotEqual(data, None)
        self.assertEqual(data['tasks']['running'], 1)
        self.assertEqual(data['tasks']['recent'], 2)
        self.assertNotEqual(data['tasks']['list'], [])
        self.assertNotEqual(data['apps']['running'], [])
        self.assertNotEqual(data['apps']['list'], [])

    @pytest.mark.usefixtures("create_pkg")
    def test_app_updates_single_ajax(self):
        self.login_as_user()

        url = '/dajaxice/upaas_admin.apps.applications.apps_updates/'
        resp = self.client.post(url, {},
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotEqual(data, {})
        self.assertNotEqual(data, None)
        self.assertEqual(data['tasks']['running'], 0)
        self.assertEqual(data['tasks']['recent'], 0)
        self.assertEqual(data['tasks']['list'], [])
        self.assertEqual(data['apps']['running'], [])
        self.assertEqual(len(data['apps']['list']), 1)
        app_data = data['apps']['list'][0]
        self.assertEqual(app_data['name'], 'redmine')
        self.assertEqual(app_data['id'], self.app.safe_id)
        self.assertEqual(app_data['is_running'], False)
        self.assertEqual(app_data['instances'], 0)
        self.assertEqual(app_data['packages'], 1)
        self.assertEqual(app_data['active_tasks'], [])

    @pytest.mark.usefixtures("create_pkg", "create_backend")
    def test_app_instances_ajax(self):
        self.login_as_user()
        url = '/dajaxice/upaas_admin.apps.applications.instances/'
        resp = self.client.post(
            url,
            data=urlencode({'argv': json.dumps({'app_id': self.app.safe_id})}),
            content_type='application/x-www-form-urlencoded',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotEqual(data, {})
        self.assertNotEqual(data, None)
        self.assertEqual(data['stats'], [])

    @pytest.mark.usefixtures("create_pkg", "create_backend")
    def test_app_instances_started_single_ajax(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan, None)

        url = '/dajaxice/upaas_admin.apps.applications.instances/'
        resp = self.client.post(
            url,
            data=urlencode({'argv': json.dumps({'app_id': self.app.safe_id})}),
            content_type='application/x-www-form-urlencoded',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotEqual(data, {})
        self.assertNotEqual(data, None)
        self.assertNotEqual(data['stats'], [])
        backend_stats = data['stats'][0]
        self.assertEqual(backend_stats['stats'], None)
        self.assertEqual(backend_stats['backend']['ip'], '127.0.0.1')
        self.assertEqual(backend_stats['backend']['name'], self.backend_name)
        self.assertEqual(backend_stats['backend']['limits'][
            'memory_per_worker_bytes'], 134217728)
        self.assertEqual(backend_stats['backend']['limits']['backend_memory'],
                         512)
        self.assertEqual(backend_stats['backend']['limits'][
            'backend_memory_bytes'], 536870912)
        self.assertEqual(backend_stats['backend']['limits'][
            'memory_per_worker'], 128)
        self.assertEqual(backend_stats['backend']['limits']['workers_min'], 1)
        self.assertEqual(backend_stats['backend']['limits']['workers_max'], 4)

    @pytest.mark.usefixtures("create_pkg", "create_backend_list")
    def test_app_instances_started_multiple_ajax(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 6, 'workers_max': 12})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan, None)

        url = '/dajaxice/upaas_admin.apps.applications.instances/'
        resp = self.client.post(
            url,
            data=urlencode({'argv': json.dumps({'app_id': self.app.safe_id})}),
            content_type='application/x-www-form-urlencoded',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertNotEqual(data, {})
        self.assertNotEqual(data, None)
        self.assertTrue(len(data['stats']) > 1)

# FIXME
    # @pytest.mark.usefixtures("create_app")
    # def test_task_messages_pending_ajax(self):
    #     self.login_as_user()
    #     url = reverse('build_package', args=[self.app.safe_id])
    #     resp = self.client.post(url, {})
    #     self.assertEqual(resp.status_code, 302)
    #     task = self.app.pending_build_tasks.first()
    #     self.assertNotEqual(task, None)
    #
    #     url = '/dajaxice/upaas_admin.apps.applications.task_messages/'
    #     resp = self.client.post(
    #         url,
    #         data=urlencode({'argv': json.dumps({'task_id': task.safe_id,
    #                                             'offset': 0})}),
    #         content_type='application/x-www-form-urlencoded',
    #         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    #     self.assertEqual(resp.status_code, 200)
    #     data = json.loads(resp.content)
    #     self.assertNotEqual(data, {})
    #     self.assertNotEqual(data, None)
    #     self.assertEqual(data['is_successful'], False)
    #     self.assertEqual(data['is_running'], False)
    #     self.assertEqual(data['is_failed'], False)
    #     self.assertEqual(data['is_finished'], False)
    #     self.assertEqual(data['is_pending'], True)
    #     self.assertEqual(data['progress'], 0)
    #     self.assertEqual(data['messages'], [])

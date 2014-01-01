# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from django.core.urlresolvers import reverse
from django.utils.html import escape

from upaas_admin.common.tests import MongoEngineTestCase


class ApplicationTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_user")
    def test_index_get(self):
        self.login_as_user()
        url = reverse('site_index')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_register_get(self):
        self.login_as_user()
        url = reverse('app_register')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_register_post(self):
        self.login_as_user()
        url = reverse('app_register')

        metadata_path = os.path.join(os.path.dirname(__file__),
                                     'meta/redmine.yml')
        with open(metadata_path, 'rb') as metadata:
            resp = self.client.post(url, {'name': 'redmine',
                                          'metadata': metadata})
            self.assertEqual(resp.status_code, 302)
            url = resp['Location']
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, 'redmine')

    @pytest.mark.usefixtures("create_app")
    def test_build_package_post(self):
        self.login_as_user()
        url = reverse('build_package', args=[self.app.safe_id])
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 302)

        url = reverse('users_tasks')
        resp = self.client.get(url)
        self.assertContains(
            resp, "Building new package for %s" % self.app_data['name'])

    @pytest.mark.usefixtures("create_app")
    def test_app_metadata_get(self):
        self.login_as_user()
        url = reverse('app_metadata', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.app_data['metadata_html'])

    @pytest.mark.usefixtures("create_app")
    def test_app_metadata_update(self):
        self.login_as_user()

        url = reverse('app_update_metadata', args=[self.app.safe_id])
        new_metadata_path = os.path.join(os.path.dirname(__file__),
                                         'meta/errbit-stable.yml')
        with open(new_metadata_path, 'rb') as new_metadata_file:
            resp = self.client.post(url, {'metadata': new_metadata_file})
            self.assertEqual(resp.status_code, 302)

        url = reverse('app_metadata', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        with open(new_metadata_path, 'rb') as new_metadata_file:
            new_metadata = new_metadata_file.read()
        self.assertContains(resp, escape(new_metadata))

    @pytest.mark.usefixtures("create_app")
    def test_app_packages_get(self):
        self.login_as_user()
        url = reverse('app_packages', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_instances_get(self):
        self.login_as_user()
        url = reverse('app_instances', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_stats_get(self):
        self.login_as_user()
        url = reverse('app_stats', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_tasks_get(self):
        self.login_as_user()
        url = reverse('app_tasks', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_start_invalid_post(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_app")
    def test_app_stop_invalid_post(self):
        self.login_as_user()
        url = reverse('app_stop', args=[self.app.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_app")
    def test_app_edit_run_plan_invalid_post(self):
        self.login_as_user()
        url = reverse('app_edit_run_plan', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 406)

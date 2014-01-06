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
    def test_index_paged_get(self):
        self.login_as_user()
        url = reverse('site_index')

        resp = self.client.get(url + '?page=1')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=a')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=10')
        self.assertEqual(resp.status_code, 404)

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
        self.assertEqual(len(self.user.applications), 1)

    @pytest.mark.usefixtures("create_app")
    def test_register_duplicated_post(self):
        self.login_as_user()
        url = reverse('app_register')

        resp = self.client.post(url, {'name': self.app_data['name'],
                                      'metadata': self.app_data['metadata']})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Application with name %s already "
                                  "registered" % self.app_data['name'])

    @pytest.mark.usefixtures("create_user")
    def test_register_invalid_post(self):
        self.login_as_user()
        url = reverse('app_register')

        resp = self.client.post(url, {'name': 'redmine'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")

        resp = self.client.post(url, {'name': 'red mine'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Name cannot contain spaces")

        resp = self.client.post(url, {'name': 'r'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Ensure this value has at least 2 characters"
                                  " (it has 1).")

        with open(__file__, 'rb') as metadata:
            resp = self.client.post(url, {'name': 'redmine',
                                          'metadata': metadata})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, escape(
            "expected '<document start>', but found "))

        metadata_path = os.path.join(os.path.dirname(__file__),
                                     'meta/invalid.yml')
        with open(metadata_path, 'rb') as metadata:
            resp = self.client.post(url, {'name': 'invalid',
                                          'metadata': metadata})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Missing required configuration entry:")

    @pytest.mark.usefixtures("create_app")
    def test_build_package_post(self):
        self.login_as_user()
        url = reverse('build_package', args=[self.app.safe_id])

        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(self.app.pending_build_tasks), 1)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(self.app.pending_build_tasks), 1)

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
    def test_app_metadata_download(self):
        self.login_as_user()

        url = reverse('app_metadata_yml', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.content, self.app_data['metadata'])

    @pytest.mark.usefixtures("create_app")
    def test_app_packages_get(self):
        self.login_as_user()
        url = reverse('app_packages', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_packages_paged_get(self):
        self.login_as_user()
        url = reverse('app_packages', args=[self.app.safe_id])

        resp = self.client.get(url + '?page=1')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=a')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=10')
        self.assertEqual(resp.status_code, 404)

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
    def test_app_tasks_paged_get(self):
        self.login_as_user()
        url = reverse('app_tasks', args=[self.app.safe_id])

        resp = self.client.get(url + '?page=1')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=a')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=10')
        self.assertEqual(resp.status_code, 404)

    @pytest.mark.usefixtures("create_app")
    def test_app_domains_get(self):
        self.login_as_user()
        url = reverse('app_domains', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_domains_paged_get(self):
        self.login_as_user()
        url = reverse('app_domains', args=[self.app.safe_id])

        resp = self.client.get(url + '?page=1')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=a')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=10')
        self.assertEqual(resp.status_code, 404)

    @pytest.mark.usefixtures("create_app")
    def test_app_assign_domain_get(self):
        self.login_as_user()
        url = reverse('app_assign_domain', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_app")
    def test_app_assign_domain_invalid_post(self):
        self.login_as_user()
        url = reverse('app_assign_domain', args=[self.app.safe_id])
        resp = self.client.post(url, {'name': 'www.google.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No TXT record for domain www.google.com')

    @pytest.mark.usefixtures("create_app")
    def test_app_start_invalid_get(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_user")
    def test_app_start_404_get(self):
        self.login_as_user()
        url = reverse('app_start', args=['123456'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    @pytest.mark.usefixtures("create_app")
    def test_app_start_invalid_post(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_app")
    def test_app_stop_invalid_get(self):
        self.login_as_user()
        url = reverse('app_stop', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_app")
    def test_app_stop_invalid_post(self):
        self.login_as_user()
        url = reverse('app_stop', args=[self.app.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_app")
    def test_app_edit_run_plan_invalid_get(self):
        self.login_as_user()
        url = reverse('app_edit_run_plan', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_user")
    def test_app_edit_run_plan_404_get(self):
        self.login_as_user()
        url = reverse('app_edit_run_plan', args=['123456'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    @pytest.mark.usefixtures("create_app")
    def test_app_edit_run_plan_invalid_post(self):
        self.login_as_user()
        url = reverse('app_edit_run_plan', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_pkg")
    @pytest.mark.usefixtures("create_backend")
    def test_app_start_edit_stop(self):
        self.login_as_user()

        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan, None)

        self.assertEqual(self.user.limits_usage['running_apps'], 1)
        self.assertEqual(self.user.limits_usage['workers'], 4)

        self.assertEqual(self.user.running_applications, [self.app])

        self.assertEqual(len(self.user.tasks), 1)
        self.assertEqual(len(self.user.recent_tasks), 1)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 406)

        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 406)

        url = reverse('app_edit_run_plan', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'workers_min': 2, 'workers_max': 3})
        self.assertEqual(resp.status_code, 302)

        url = reverse('app_stop', args=[self.app.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 302)

    @pytest.mark.usefixtures("create_app")
    def test_app_interpreter_version_from_app_method(self):
        self.assertEqual(self.app.interpreter_version, '2.0.0')

    @pytest.mark.usefixtures("create_pkg")
    def test_app_interpreter_version_from_pkg_method(self):
        self.assertEqual(self.app.interpreter_version, '2.0.0')

    @pytest.mark.usefixtures("create_pkg")
    def test_app_trim_package_files_one_method(self):
        self.app.trim_package_files()

    @pytest.mark.usefixtures("create_pkg_list")
    def test_app_trim_package_files_many_method(self):
        self.app.trim_package_files()

    @pytest.mark.usefixtures("create_pkg_list")
    def test_app_remove_unpacked_packages_method(self):
        self.app.remove_unpacked_packages()

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.applications.models import Package
from upaas_admin.apps.applications.exceptions import UnpackError


class PackageTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_details_get(self):
        self.login_as_user()
        self.pkg.metadata += '\n# 123456789'
        self.pkg.save()
        url = reverse('package_details', args=[self.pkg.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.pkg.safe_id)
        self.assertContains(resp, '# 123456789')

    @pytest.mark.usefixtures("create_app")
    def test_pkg_details_404_get(self):
        self.login_as_user()
        url = reverse('package_details', args=['1234'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_delete_get(self):
        self.login_as_user()
        url = reverse('package_delete', args=[self.pkg.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_delete_invalid_post(self):
        self.login_as_user()
        url = reverse('package_delete', args=[self.pkg.safe_id])
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_delete_current_post(self):
        self.login_as_user()
        url = reverse('package_delete', args=[self.pkg.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_pkg_list")
    def test_pkg_delete_post(self):
        self.login_as_user()
        pkg = self.pkg_list[len(self.pkg_list)-1]
        url = reverse('package_delete', args=[pkg.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Package.objects(id=pkg.id).first(), None)

    @pytest.mark.usefixtures("create_pkg_list")
    def test_pkg_rollback_get(self):
        self.login_as_user()
        pkg = self.pkg_list[len(self.pkg_list)-1]
        url = reverse('package_rollback', args=[pkg.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_rollback_current_post(self):
        self.login_as_user()
        url = reverse('package_rollback', args=[self.pkg.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 406)

    @pytest.mark.usefixtures("create_pkg_list")
    def test_pkg_rollback_post(self):
        self.login_as_user()
        pkg = self.pkg_list[len(self.pkg_list)-1]
        url = reverse('package_rollback', args=[pkg.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertEqual(self.app.current_package.id, pkg.id)

    @pytest.mark.usefixtures("create_pkg")
    def test_app_metadata_from_pkg_get(self):
        self.login_as_user()
        url = reverse('app_meta_from_pkg', args=[self.pkg.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_pkg")
    def test_app_metadata_from_pkg_post(self):
        self.login_as_user()

        app_meta = self.app.metadata + '\n# 1234567890'
        self.app.metadata = app_meta
        self.app.save()
        self.assertEqual(self.app.metadata, app_meta)

        url = reverse('app_meta_from_pkg', args=[self.pkg.safe_id])
        resp = self.client.post(url, {'confirm': True})
        self.assertEqual(resp.status_code, 302)

        self.app.reload()
        self.assertEqual(self.app.metadata, self.pkg.metadata)

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_metadata_download(self):
        self.login_as_user()

        url = reverse('pkg_metadata_yml', args=[self.pkg.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.content, self.app_data['metadata'])

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_metadata_config_method(self):
        self.assertNotEqual(self.pkg.metadata_config, {})

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_package_path_method(self):
        self.assertEqual(self.pkg.package_path, '/tmp/%s' % self.pkg.safe_id)

    @pytest.mark.usefixtures("create_pkg")
    def test_uwsgi_options_from_metadata_method(self):
        self.assertEqual(self.pkg.uwsgi_options_from_metadata(),
                         ['route = ^/ basicauth:UPAAS,admin:adm123'])

    @pytest.mark.usefixtures("create_pkg_with_custom_domain", "create_backend",
                             "create_router")
    def test_generate_uwsgi_config_method(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan.backends, [])
        config = self.pkg.generate_uwsgi_config(self.app.run_plan.backends[0])
        self.assertNotEqual(config, [])
        self.assertTrue('[uwsgi]' in config)
        self.assertTrue('var_app_name = redmine' in config)
        self.assertTrue('var_app_id = %s' % self.app.safe_id in config)
        self.assertTrue('env = REDMINE_LANG=en' in config)
        skey = 'subscribe2 = server=%s:%d,key=%s' % (
            self.router.subscription_ip, self.router.subscription_port,
            self.domain.name)
        self.assertTrue(skey in config)
        self.assertTrue('cron = -1 20 30 1 -1 ping' in config)
        self.assertTrue('cron = -1 -1 -1 -1 -1 pong' in config)
        self.assertTrue('env = UPAAS_STORAGE_MOUNTPOINT=/storage' in config)

    @pytest.mark.usefixtures("create_pkg", "create_backend", "create_router")
    def test_save_vassal_config_method(self):
        self.login_as_user()
        url = reverse('app_start', args=[self.app.safe_id])
        resp = self.client.post(url, {'workers_min': 1, 'workers_max': 4})
        self.assertEqual(resp.status_code, 302)
        self.app.reload()
        self.assertNotEqual(self.app.run_plan.backends, [])
        self.pkg.save_vassal_config(self.app.run_plan.backends[0])
        ini_path = '/tmp/%s.ini' % self.app.safe_id
        self.assertEqual(os.path.isfile(ini_path), True)
        mtime1 = os.path.getmtime(ini_path)
        self.pkg.save_vassal_config(self.app.run_plan.backends[0])
        mtime2 = os.path.getmtime(ini_path)
        if os.path.isfile(ini_path):
            os.unlink(ini_path)
        self.assertEqual(mtime1, mtime2)

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_unpack_missing_method(self):
        with pytest.raises(UnpackError):
            self.pkg.unpack()

    @pytest.mark.usefixtures("create_pkg")
    def test_pkg_delete_package_file_missing_method(self):
        self.pkg.delete_package_file()

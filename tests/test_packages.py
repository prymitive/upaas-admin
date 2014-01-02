# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.applications.models import Package


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

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.urlresolvers import reverse
from django.utils.html import escape

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.users.models import User
from upaas_admin.apps.scheduler.models import UserLimits
from upaas_admin.apps.servers.models import RouterServer, BackendServer


class AdminTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_user")
    def test_superuser_required_get(self):
        self.login_as_user()
        for name in ['admin_users_list', 'admin_user_create',
                     'admin_routers_list', 'admin_router_create',
                     'admin_backends_list', 'admin_backend_create']:
            url = reverse(name)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    @pytest.mark.usefixtures("create_user")
    def test_superuser_required_user_post(self):
        self.login_as_user()
        for name in ['admin_user_edit', 'admin_user_limits_create',
                     'admin_user_limits_edit', 'admin_user_limits_delete']:
            url = reverse(name, args=[self.user.safe_id])
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    @pytest.mark.usefixtures("create_user")
    @pytest.mark.usefixtures("create_router")
    def test_superuser_required_router_post(self):
        self.login_as_user()
        url = reverse('admin_router_edit', args=[self.router.name])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    @pytest.mark.usefixtures("create_user")
    @pytest.mark.usefixtures("create_backend")
    def test_superuser_required_backend_post(self):
        self.login_as_user()
        url = reverse('admin_backend_edit', args=[self.backend.name])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_users_list_get(self):
        self.login_as_user()
        url = reverse('admin_users_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_user_create_get(self):
        self.login_as_user()
        url = reverse('admin_user_create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_user_create_invalid_post(self):
        self.login_as_user()
        url = reverse('admin_user_create')
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_user_create_edit_delete(self):
        self.login_as_user()

        url = reverse('admin_user_create')
        resp = self.client.post(url, {'username': 'newuser',
                                      'first_name': 'FirstŁÓŹĆ',
                                      'last_name': 'ĘĆŚŻName',
                                      'email': 'newuser@domain.com',
                                      'is_active': False,
                                      'is_superuser': True,
                                      'password': '123456789'})
        self.assertEqual(resp.status_code, 302)
        u = User.objects(username='newuser').first()
        self.assertNotEqual(u, None)
        self.assertEqual(u.username, 'newuser')
        self.assertEqual(u.first_name, 'FirstŁÓŹĆ')
        self.assertEqual(u.last_name, 'ĘĆŚŻName')
        self.assertEqual(u.email, 'newuser@domain.com')
        self.assertEqual(u.is_active, False)
        self.assertEqual(u.is_superuser, True)

        url = reverse('admin_user_edit', args=[u.safe_id])
        resp = self.client.post(url, {'first_name': 'NewFirstŁÓŹĆ',
                                      'last_name': 'NewĘĆŚŻName',
                                      'email': 'newuser@domain.com',
                                      'is_active': True,
                                      'is_superuser': False})
        self.assertEqual(resp.status_code, 302)
        u.reload()
        self.assertEqual(u.first_name, 'NewFirstŁÓŹĆ')
        self.assertEqual(u.last_name, 'NewĘĆŚŻName')
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_superuser, False)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_user_limits_create_get(self):
        self.login_as_user()

        url = reverse('admin_user_limits_create', args=[self.user.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_user_limits_create_invalid_post(self):
        self.login_as_user()
        url = reverse('admin_user_limits_create', args=[self.user.safe_id])
        resp = self.client.post(url, {'running_apps': -4,
                                      'memory_per_worker': 0,
                                      'workers': 0,
                                      'packages_per_app': -4})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Ensure this value is greater than or equal")

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_user_limits_create_edit_delete(self):
        self.login_as_user()

        url = reverse('admin_user_limits_create', args=[self.user.safe_id])
        resp = self.client.post(url, {'running_apps': 0,
                                      'memory_per_worker': 16,
                                      'workers': 8,
                                      'packages_per_app': 4})
        self.assertEqual(resp.status_code, 302)
        l = UserLimits.objects(user=self.user).first()
        self.assertNotEqual(l, None)
        self.assertEqual(l.running_apps, 0)
        self.assertEqual(l.memory_per_worker, 16)
        self.assertEqual(l.workers, 8)
        self.assertEqual(l.packages_per_app, 4)

        url = reverse('admin_user_limits_edit', args=[l.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'running_apps': 2,
                                      'memory_per_worker': 32,
                                      'workers': 4,
                                      'packages_per_app': 2})
        self.assertEqual(resp.status_code, 302)
        l.reload()
        self.assertEqual(l.running_apps, 2)
        self.assertEqual(l.memory_per_worker, 32)
        self.assertEqual(l.workers, 4)
        self.assertEqual(l.packages_per_app, 2)

        url = reverse('admin_user_limits_delete', args=[l.safe_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(UserLimits.objects(user=self.user).first(), None)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_routers_list_get(self):
        self.login_as_user()
        url = reverse('admin_routers_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_router_create_get(self):
        self.login_as_user()
        url = reverse('admin_router_create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_router_create_invalid_post(self):
        self.login_as_user()
        url = reverse('admin_router_create')
        resp = self.client.post(url, {'is_enabled': True,
                                      'public_ip': '123.456.789.876'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")
        self.assertContains(
            resp, escape("single byte must be 0 <= byte < 256"))

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_router_create_edit_delete(self):
        self.login_as_user()

        url = reverse('admin_router_create')
        resp = self.client.post(url, {'is_enabled': False, 'name': 'router1',
                                      'public_ip': '8.8.8.8',
                                      'private_ip': '127.0.0.1',
                                      'subscription_port': 3333})
        self.assertEqual(resp.status_code, 302)
        router = RouterServer.objects(name='router1').first()
        self.assertNotEqual(router, None)
        self.assertEqual(router.name, 'router1')
        self.assertEqual(router.is_enabled, False)
        self.assertEqual(router.public_ip.strNormal(), '8.8.8.8')
        self.assertEqual(router.private_ip.strNormal(), '127.0.0.1')
        self.assertEqual(router.subscription_port, 3333)

        url = reverse('admin_router_edit', args=[router.name])
        resp = self.client.post(url, {'is_enabled': True, 'name': 'router2',
                                      'public_ip': '7.7.7.7',
                                      'private_ip': '127.0.0.2',
                                      'subscription_port': 4444})
        self.assertEqual(resp.status_code, 302)
        router.reload()
        self.assertEqual(router.name, 'router2')
        self.assertEqual(router.is_enabled, True)
        self.assertEqual(router.public_ip.strNormal(), '7.7.7.7')
        self.assertEqual(router.private_ip.strNormal(), '127.0.0.2')
        self.assertEqual(router.subscription_port, 4444)

        router.delete()
        self.assertEqual(RouterServer.objects().first(), None)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_backends_list_get(self):
        self.login_as_user()
        url = reverse('admin_backends_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_backend_create_get(self):
        self.login_as_user()
        url = reverse('admin_backend_create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_backend_create_invalid_post(self):
        self.login_as_user()
        url = reverse('admin_backend_create')
        resp = self.client.post(url, {'is_enabled': True,
                                      'ip': '123.456.789.876'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")
        self.assertContains(
            resp, escape("single byte must be 0 <= byte < 256"))

    @pytest.mark.usefixtures("create_superuser")
    def test_admin_backend_create_edit_delete(self):
        self.login_as_user()

        url = reverse('admin_backend_create')
        resp = self.client.post(url, {'is_enabled': False, 'name': 'backend1',
                                      'ip': '8.8.8.8'})
        self.assertEqual(resp.status_code, 302)
        backend = BackendServer.objects(name='backend1').first()
        self.assertNotEqual(backend, None)
        self.assertEqual(backend.name, 'backend1')
        self.assertEqual(backend.is_enabled, False)
        self.assertEqual(backend.ip.strNormal(), '8.8.8.8')

        url = reverse('admin_backend_edit', args=[backend.name])
        resp = self.client.post(url, {'is_enabled': True, 'name': 'backend2',
                                      'ip': '7.7.7.7'})
        self.assertEqual(resp.status_code, 302)
        backend.reload()
        self.assertEqual(backend.name, 'backend2')
        self.assertEqual(backend.is_enabled, True)
        self.assertEqual(backend.ip.strNormal(), '7.7.7.7')

        backend.delete()
        self.assertEqual(BackendServer.objects().first(), None)

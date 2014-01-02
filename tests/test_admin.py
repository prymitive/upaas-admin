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

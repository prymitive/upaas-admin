# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase


class UserTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_user")
    def test_user_creation(self):
        self.assertEqual(self.user.username, self.user_data['login'])
        self.assertEqual(self.user.first_name, self.user_data['first_name'])
        self.assertEqual(self.user.last_name, self.user_data['last_name'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertFalse(self.user.is_superuser)

    def test_login_view_get(self):
        url = reverse('site_login')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'You need to login to access this page')

    @pytest.mark.usefixtures("create_user")
    def test_login_view_post(self):
        url = reverse('site_login')
        resp = self.client.post(url, {'username': self.user_data['login'],
                                      'password': self.user_data['password']})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver/')

    def test_login_view_post_invalid(self):
        url = reverse('site_login')
        resp = self.client.post(url, {'username': 'invalid',
                                      'password': 'invalid'})
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_api_key_get(self):
        self.login_as_user()
        url = reverse('users_profile')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'apikey-input')
        self.assertContains(resp, self.user.apikey)

    @pytest.mark.usefixtures("create_user")
    def test_api_key_invalid_reset(self):
        self.login_as_user()

        url = reverse('users_apikey_reset')
        resp = self.client.post(url, {'apikey': '12345'})
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_api_key_reset(self):
        self.login_as_user()
        old_apikey = self.user.apikey

        url = reverse('users_apikey_reset')
        resp = self.client.post(url, {'apikey': old_apikey})
        self.assertEqual(resp.status_code, 302)

        self.user.reload()

        url = reverse('users_profile')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'apikey-input')
        self.assertNotContains(resp, old_apikey)
        self.assertContains(resp, self.user.apikey)

    @pytest.mark.usefixtures("create_user")
    def test_password_change(self):
        self.login_as_user()
        new_password = 'myNewPassw0rd'

        url = reverse('password')
        resp = self.client.post(url, {
            'old_password': self.user_data['password'],
            'new_password1': new_password,
            'new_password2': new_password})
        self.assertEqual(resp.status_code, 302)

        url = reverse('site_login')

        resp = self.client.post(url, {'username': self.user_data['login'],
                                      'password': self.user_data['password']})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'username': self.user_data['login'],
                                      'password': new_password})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver/')

    @pytest.mark.usefixtures("create_user")
    def test_limits_get(self):
        self.login_as_user()
        url = reverse('users_limits')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_tasks_get(self):
        self.login_as_user()
        url = reverse('users_tasks')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_tasks_paged_get(self):
        self.login_as_user()
        url = reverse('users_tasks')

        resp = self.client.get(url + '?page=1')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=a')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + '?page=10')
        self.assertEqual(resp.status_code, 404)

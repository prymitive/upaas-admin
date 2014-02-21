# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.urlresolvers import reverse
from django.core import mail
from django.utils.html import escape

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.users.models import User


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
            'new_password1': '12345678',
            'new_password2': '12345678'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp,
                            escape("Based on a common sequence of characters"))

        resp = self.client.post(url, {
            'old_password': self.user_data['password'],
            'new_password1': 'hvax',
            'new_password2': 'hvax'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, escape("Must be more complex"))

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

    def test_user_model_apikey_class_meth(self):
        apikey = User.generate_apikey()
        self.assertNotEqual(apikey, None)
        self.assertEqual(len(apikey), 40)

    @pytest.mark.usefixtures("create_user")
    def test_user_model_full_name_or_login_meth(self):
        self.assertEqual(self.user.full_name_or_login,
                         self.user.get_full_name())
        self.user.first_name = None
        self.user.last_name = None
        self.user.save()
        self.assertEqual(self.user.full_name_or_login, self.user.username)

    @pytest.mark.usefixtures("create_user")
    def test_password_reset_invalid_email(self):
        url = reverse('password_reset')

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'email': 'invalid@email.xyz'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'],
                         'http://testserver' + reverse('password_reset_sent'))
        self.assertEqual(len(mail.outbox), 0)

    @pytest.mark.usefixtures("create_user")
    def test_password_reset_invalid_token(self):
        url = reverse('password_reset_confirm', args=['abcdef987', '12345xyz'])

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This reset link is no longer valid")

    @pytest.mark.usefixtures("create_user")
    def test_password_reset_invalid_uidb(self):
        url = reverse('password_reset_confirm',
                      args=['NTJhNDc5xxOWE1YmE3MmUwZmNhZDA5MzEy', '12345xyz'])

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    @pytest.mark.usefixtures("create_user")
    def test_password_reset(self):
        url = reverse('password_reset')

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {'email': 'email@domain.com'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'],
                         'http://testserver' + reverse('password_reset_sent'))
        self.assertEqual(len(mail.outbox), 1)

        link = None
        for line in mail.outbox[0].body.splitlines():
            if line.startswith('http://'):
                link = line.rstrip('\n')
        self.assertNotEqual(link, None)
        url = link.replace('http://testserver', '')

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")

        resp = self.client.post(url, {'new_password1': '12345678'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")

        resp = self.client.post(url, {'new_password2': '12345678'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required.")

        resp = self.client.post(url, {'new_password1': 'fGarEQ733jSGt2YmB4UH',
                                      'new_password2': 'fGarEQ733jSGt2YmB4Ux'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp,
                            escape("The two password fields didn't match."))

        resp = self.client.post(url, {'new_password1': '12345678',
                                      'new_password2': '12345678'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp,
                            escape("Based on a common sequence of characters"))

        resp = self.client.post(url, {'new_password1': 'hvax',
                                      'new_password2': 'hvax'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, escape("Must be more complex"))

        resp = self.client.post(url, {'new_password1': 'fGarEQ733jSGt2YmB4UH',
                                      'new_password2': 'fGarEQ733jSGt2YmB4UH'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'],
            'http://testserver' + reverse('password_reset_complete'))

        url = reverse('password_reset_complete')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        url = reverse('site_login')
        resp = self.client.post(url, {'username': self.user_data['login'],
                                      'password': 'fGarEQ733jSGt2YmB4UH'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver/')

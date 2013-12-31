# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.users.models import User


class UserTest(MongoEngineTestCase):

    LOGIN = 'testlogin'
    FIRST_NAME = 'ąćźółęż'
    LAST_NAME = 'CAPITAL'
    EMAIL = 'email@domain.com'
    PASSWORD = '123456789źćż'

    def create_user(self):
        u = User.objects(username=self.LOGIN).first()
        if u:
            u.delete()

        u = User(username=self.LOGIN, first_name=self.FIRST_NAME,
                 last_name=self.LAST_NAME, email=self.EMAIL,
                 is_superuser=False)
        u.set_password(self.PASSWORD)
        u.save()

        return u

    def test_user_creation(self):
        u = self.create_user()

        self.assertEqual(u.username, self.LOGIN)
        self.assertEqual(u.first_name, self.FIRST_NAME)
        self.assertEqual(u.last_name, self.LAST_NAME)
        self.assertEqual(u.email, self.EMAIL)
        self.assertFalse(u.is_superuser)
        u.delete()

    def test_login_view_get(self):
        url = reverse('site_login')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'You need to login to access this page')

    def test_login_view_post(self):
        u = self.create_user()
        url = reverse('site_login')
        resp = self.client.post(url, {'username': self.LOGIN,
                                      'password': self.PASSWORD})

        self.assertEqual(302, resp.status_code)
        u.delete()

    def test_api_key_get(self):
        u = self.create_user()
        self.client.login(username=self.LOGIN, password=self.PASSWORD)

        url = reverse('users_profile')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'apikey-input')
        self.assertContains(resp, u.apikey)
        u.delete()

    def test_api_key_reset(self):
        u = self.create_user()
        self.client.login(username=self.LOGIN, password=self.PASSWORD)
        old_apikey = u.apikey

        url = reverse('users_apikey_reset')
        resp = self.client.post(url, {'apikey': old_apikey})
        self.assertEqual(resp.status_code, 302)

        u.reload()

        url = reverse('users_profile')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'apikey-input')
        self.assertNotContains(resp, old_apikey)
        self.assertContains(resp, u.apikey)
        u.delete()

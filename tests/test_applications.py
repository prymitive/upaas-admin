# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase


class ApplicationTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_user")
    def test_index_get(self):
        self.client.login(username=self.user_data['login'],
                          password=self.user_data['password'])
        url = reverse('site_index')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_register_get(self):
        self.client.login(username=self.user_data['login'],
                          password=self.user_data['password'])
        url = reverse('app_register')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_register_post(self):
        self.client.login(username=self.user_data['login'],
                          password=self.user_data['password'])
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

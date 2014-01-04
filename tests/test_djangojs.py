# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.urlresolvers import reverse

from upaas_admin.common.tests import MongoEngineTestCase


class DjangoJSTest(MongoEngineTestCase):

    def test_js_init_anonymous_get(self):
        url = reverse('django_js_init')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_js_init_user_get(self):
        self.login_as_user()
        url = reverse('django_js_init')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_urls_anonymous_get(self):
        url = reverse('django_js_urls')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_urls_user_get(self):
        self.login_as_user()
        url = reverse('django_js_urls')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_context_anonymous_get(self):
        url = reverse('django_js_context')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_context_user_get(self):
        self.login_as_user()
        url = reverse('django_js_context')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_catalog_anonymous_get(self):
        url = reverse('js_catalog')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @pytest.mark.usefixtures("create_user")
    def test_catalog_user_get(self):
        self.login_as_user()
        url = reverse('js_catalog')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

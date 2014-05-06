# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.template import Context, Template
from django.test.client import RequestFactory

from upaas_admin.common.tests import MongoEngineTestCase


class TemplateTagsTest(MongoEngineTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_mb_to_bytes(self):
        ctx = Context({'request': self.request,
                       'bytes': 4.5})
        t = Template('{% load upaas_mb_to_bytes %}{{ bytes|mb_to_bytes }}')
        self.assertEqual(t.render(ctx), '4718592.0')

    def inline_truncate(self, value, expected):
        ctx = Context({'request': self.request,
                       'text': 'abcdefghijklmnopqrstuvwxyz'})
        t = Template('{%% load upaas_inline_truncate %%}'
                     '{{ text|inline_truncate:%d }}' % value)
        ret = t.render(ctx)
        self.assertEqual(ret, expected)
        self.assertEqual(len(ret), value)

    def test_inline_truncate_zero(self):
        self.inline_truncate(0, '')

    def test_inline_truncate_one(self):
        self.inline_truncate(1, 'a')

    def test_inline_truncate_too_small(self):
        self.inline_truncate(4, 'abcd')

    def test_inline_truncate_smallest(self):
        self.inline_truncate(5, 'a...z')

    def test_inline_truncate_nine(self):
        self.inline_truncate(9, 'abc...xyz')

    def test_inline_truncate_helf(self):
        self.inline_truncate(15, 'abcdef...uvwxyz')

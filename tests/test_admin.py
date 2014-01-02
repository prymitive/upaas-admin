# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.core.management import call_command

from upaas_admin.common.tests import MongoEngineTestCase


class AdminTest(MongoEngineTestCase):

    def test_create_indexes_cmd(self):
        self.assertEqual(call_command('create_indexes'), None)

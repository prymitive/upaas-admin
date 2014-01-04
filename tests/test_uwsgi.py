# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas_admin.common.tests import MongoEngineTestCase


class UWSGITest(MongoEngineTestCase):

    def test_uwsgi_stats_invalid(self):
        from upaas_admin.common.uwsgi import fetch_json_stats
        self.assertEqual(fetch_json_stats('127.0.0.1', 65000), None)

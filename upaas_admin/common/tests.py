# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

# based on:
# http://nubits.org/post/django-mongodb-mongoengine-testing-with-custom-
# test-runner/


from __future__ import unicode_literals

import time

from mongoengine import connect
from mongoengine.connection import disconnect

from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner


class MongoEngineTestRunner(DjangoTestSuiteRunner):

    mongodb_name = "testrun-%d" % time.time()

    def setup_databases(self, **kwargs):
        disconnect()
        connect(self.mongodb_name)
        return super(MongoEngineTestRunner, self).setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        from mongoengine.connection import get_connection, disconnect
        connection = get_connection()
        connection.drop_database(self.mongodb_name)
        disconnect()
        super(MongoEngineTestRunner, self).teardown_databases(old_config,
                                                              **kwargs)


class MongoEngineTestCase(TestCase):

    def _fixture_setup(self):
        pass

    def _fixture_teardown(self):
        pass

# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.core import mail

from upaas_admin.common.tests import MongoEngineTestCase


class SMTPTest(MongoEngineTestCase):

    def test_send_email(self):
        mail.send_mail('Subject', 'Test message', 'from@u-paas.org',
                       ['to@u-paas.org'], fail_silently=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Subject')

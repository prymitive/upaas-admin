# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from django.core.management import call_command

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.admin.management.commands.migrate_db import (
    OldApplication, OldApplicationDomain, Application, ApplicationDomain)


class DomainMigrationTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_user")
    def test_migration(self):

        with open(os.path.join(os.path.dirname(__file__), 'meta/redmine.yml'),
                  'rb') as m:
            metadata = m.read()

        no_domain_apps = []
        for i in range(0, 10):
            app = OldApplication(name='app%d' % i, owner=self.user,
                                 metadata=metadata)
            app.save()
            no_domain_apps.append(app.name)

        app = OldApplication(name='app', owner=self.user, metadata=metadata)

        domains = {}
        for i in range(0, 10):
            name = 'domain%d' % i
            validated = (i % 2)
            domains[name] = validated
            domain = OldApplicationDomain(name=name, validated=validated)
            app.old_domains.append(domain)

        app.save()

        app = OldApplication.objects(name='app').first()

        self.assertEqual(len(app.old_domains), 10)
        self.assertEqual(call_command('migrate_db'), None)
        app.reload()
        self.assertEqual(len(app.old_domains), 0)
        self.assertEqual(len(ApplicationDomain.objects(application=app)), 10)

        new_app = Application.objects(name='app').first()
        self.assertEqual(len(new_app.custom_domains), 10)
        for domain in new_app.custom_domains:
            self.assertTrue(domain.name in domains)
            self.assertEqual(domain.validated, domains[domain.name])

        self.assertEqual(
            len(ApplicationDomain.objects(application=new_app)), 10)
        for name, validated in domains.items():
            domain = ApplicationDomain.objects(application=app,
                                               name=name).first()
            self.assertNotEqual(domain, None)
            self.assertEqual(domain.validated, validated)

        app.delete()

        for name in no_domain_apps:
            app = Application.objects(name=name).first()
            self.assertNotEqual(app, None)
            self.assertEqual(len(app.custom_domains), 0)
            app.delete()

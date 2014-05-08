# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import datetime
import logging

from mongoengine import (Document, EmbeddedDocument, QuerySetManager,
                         DateTimeField, StringField, BooleanField, ListField,
                         EmbeddedDocumentField, NotUniqueError)

from django.core.management.base import BaseCommand

from upaas_admin.common.fields import IPv4Field
from upaas_admin.apps.applications.models import Application, ApplicationDomain
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.servers.models import RouterServer


log = logging.getLogger("migrate_db")


class OldApplicationDomain(EmbeddedDocument):
    date_created = DateTimeField(required=True,
                                 default=datetime.datetime.now)
    name = StringField(required=True)
    validated = BooleanField()


class OldApplication(Document):
    name = StringField()
    old_domains = ListField(EmbeddedDocumentField(OldApplicationDomain),
                            db_field='domains')
    _default_manager = QuerySetManager()
    meta = {'collection': 'application'}


class OldRouterServer(Document):
    name = StringField(required=True, max_length=60, unique=True)
    private_ip = IPv4Field()
    public_ip = IPv4Field()
    meta = {'collection': 'router_server'}


class Command(BaseCommand):

    help = 'Migrate database after upgrade'

    def migrate_domains(self):
        done = 0
        errors = 0
        for app in OldApplication.objects():
            new_app = Application.objects(id=app.id).first()
            for old_domain in app.old_domains:
                log.info("Migrating domain: %s / %s" % (app.name,
                                                        old_domain.name))
                domain = ApplicationDomain(
                    application=new_app, name=old_domain.name,
                    date_created=old_domain.date_created,
                    validated=old_domain.validated)
                try:
                    domain.save()
                except NotUniqueError:
                    log.error("Domain %s already exists, it was NOT migrated")
                    errors += 1
                else:
                    done += 1
            app.update(unset__old_domains=True)
        if done or errors:
            log.info("%d domain(s) migrated, %d error(s)" % (done, errors))

    def migrate_run_plans(self):
        for run_plan in ApplicationRunPlan.objects():
            if not run_plan.application.run_plan:
                log.info(
                    "Migrating run plan for %s" % run_plan.application.name)
                run_plan.application.update(set__run_plan=run_plan)

    def migrate_routers(self):
        for router in OldRouterServer.objects():
            if router.private_ip:
                log.info("Migrating router: %s" % router.name)
                RouterServer.objects(name=router.name).update_one(
                    set__subscription_ip=router.private_ip)
                router.update(unset__public_ip=True, unset__private_ip=True)

    def handle(self, *args, **options):
        self.migrate_domains()
        self.migrate_run_plans()
        self.migrate_routers()

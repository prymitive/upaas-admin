# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import datetime
import logging

from mongoengine import (Document, EmbeddedDocument, QuerySetManager,
                         DateTimeField, StringField, BooleanField, ListField,
                         EmbeddedDocumentField, NotUniqueError)

from django.core.management.base import BaseCommand

from upaas_admin.apps.applications.models import Application, ApplicationDomain


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


class Command(BaseCommand):

    help = 'Create missing MongoDB indexes'

    def migrate_domains(self):
        done = 0
        errors = 0
        for app in OldApplication.objects():
            new_app = Application.objects(id=app.id).first()
            log.info("Application: %s" % app.name)
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
        log.info("%d domain(s) migrated, %d error(s)" % (done, errors))

    def handle(self, *args, **options):
        self.migrate_domains()
